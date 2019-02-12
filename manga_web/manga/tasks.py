from __future__ import absolute_import, unicode_literals
import os
import logging
import shlex
import shutil
import subprocess
import time

from django.conf import settings
from django.core.mail import send_mail
from celery import group, chain
from celery.decorators import task
from PIL import Image
import boto3
import requests

from .utils import url2filename, extract_images_url
from .models import Volume, Chapter


BUCKET_NAME = settings.BUCKET_NAME
VENV_PATH = settings.VENV_PATH
# https://stackoverflow.com/questions/31784484/how-to-parallelized-file-downloads
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# s3 = boto3.resource('s3')

logger = logging.getLogger("Manga celery")
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(fmt)

logger.addHandler(handler)


def download(chapter_id, index, path, url):
    filename = url2filename(url, chapter_id, index)
    logging.debug('downloading %s', filename)
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(os.path.join(path, filename), 'wb') as f:
            for chunk in r:
                f.write(chunk)


def generate_key(vol):
    return "{0} - Volume {1}.mobi".format(vol.manga.name, vol.number)


def make_download_link(file_name):
    bucket_location = boto3.client('s3').get_bucket_location(Bucket=BUCKET_NAME)
    url = "https://s3-{0}.amazonaws.com/{1}/{2}".format(
        bucket_location['LocationConstraint'],
        BUCKET_NAME,
        file_name
    )
    return url


def make_volume_dir(volume_id):
    v = Volume.objects.get(id=volume_id)
    path = os.path.join('/tmp/Manga', v.__str__())
    os.makedirs(path, exist_ok=True)
    return path


def extract_chapters(volume_id):
    v = Volume.objects.get(id=volume_id)
    chapters = v.chapter_set.all()
    return chapters


@task(name="download_chapter")
def download_chapter(path, chapter_id):
    c = Chapter.objects.get(id=chapter_id)
    urls = extract_images_url(c.source, c.web_source)
    for index, url in enumerate(urls):
        download(chapter_id, index, path, url)


@task(name="download_volume")
def download_volume(volume_id):
    path = make_volume_dir(volume_id)
    chapters = extract_chapters(volume_id)
    g = group(download_chapter.si(path, chap.id) for chap in chapters)()
    return path


@task(name="generate_manga")
def generate_manga(path, profile='KV'):
    time.sleep(120)
    args = shlex.split('{0}/kcc-c2e -m -q -p {1} -f MOBI {2}'.format(
        VENV_PATH,
        profile,
        shlex.quote(path)
    ))
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.communicate()
    return "{}.mobi".format(path)


@task(name="delete_corrupt_file")
def delete_corrupt_file(path):
    time.sleep(30)
    for filename in os.listdir(path):
        try:
            img = Image.open(os.path.join(path, filename))
            img.verify()
        except (IOError, SyntaxError) as e:
            os.remove(os.path.join(path, filename))
            logger.info("Removed corrupted image {}".format(os.path.join(path, filename)))

    return path


# def upload(path, file_name):
#     time.sleep(30)
#     with open(path, 'rb') as f:
#         obj = s3.Bucket(BUCKET_NAME).put_object(Key=file_name, Body=f)
#         return obj


def fshare_upload(path, volume):
    from get_fshare import FSAPI
    from unidecode import unidecode

    bot = FSAPI(settings.FSHARE_EMAIL, settings.FSHARE_PASSWORD)
    bot.login()
    try:
        result = bot.upload(
            path,
            "/KindleManga/{}/{}".format(volume.manga.web_source, unidecode(volume.manga.name))
        )
        return result
    except Exception as e:
        logger.error(e)


@task(name="upload_and_save")
def upload_and_save(path, volume_id):
    v = Volume.objects.get(id=volume_id)
    r = fshare_upload(path, v)
    logger.debug(path)
    logger.debug(r)
    link = r.get('url')
    v.fshare_link = link
    v.save()
    shutil.rmtree(path.split('.mobi')[0])
    os.remove(path)
    return v.manga.name


# @task(name="upload_and_save")
# def upload_and_save(path, volume_id):
#     v = Volume.objects.get(id=volume_id)
#     file_name = generate_key(v)
#     r = upload(path, file_name)
#     link = make_download_link(file_name)
#     v.download_link = link
#     v.save()
#     shutil.rmtree(path.split('.mobi')[0])
#     os.remove(path)
#     return v.manga.name


@task(name="send_notification")
def send_notification(volume_id, email):
    v = Volume.objects.get(id=volume_id)
    send_mail(
        '[Kindlemanga.xyz] {} - Volume {} has been converted'.format(v.manga.name, v.number),
        'Hello {0}, your manga: {1} - Volume {2} has been converted successful. Please check it at {3}'.format(
            email, v.manga.name, v.number, 'https://kindlemanga.xyz' + v.manga.get_absolute_url()
        ),
        os.getenv('GMAIL_EMAIL', 'kindlemanga.xyz@gmail.com'),
        [email, ]
    )
    logger.debug("Send email to {} succeed".format(email))

    if settings.PUSHOVER_ENABLE:
        requests.post("https://api.pushover.net/1/messages.json", data = {
            "token": os.getenv("PUSHOVER_APP_TOKEN"),
            "user": os.getenv("PUSHOVER_USER_KEY"),
            "message": "Convert manga {} - volume {} succeed. User email: {}".format(
                v.manga.name, v.number, email
            )
        })


def make_volume(volume_id, email):
    res = chain(
        download_volume.s(volume_id),
        delete_corrupt_file.s(),
        generate_manga.s(),
        upload_and_save.s(volume_id),
        send_notification.si(volume_id, email)
    )()
    return res
