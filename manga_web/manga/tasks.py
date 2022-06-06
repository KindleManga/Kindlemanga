import logging
import os
import shlex
import shutil
import subprocess

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.core.files.base import File
from main.celery import app
from PIL import Image

from .models import Chapter, Volume
from .utils import extract_images_url, url2filename

BUCKET_NAME = settings.BUCKET_NAME
# https://stackoverflow.com/questions/31784484/how-to-parallelized-file-downloads
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


logger = logging.getLogger("Manga celery")
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(fmt)

logger.addHandler(handler)


def download(chapter_id, index, path, url):
    filename = url2filename(url, chapter_id, index)
    logging.debug("downloading %s", filename)
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(os.path.join(path, filename), "wb") as f:
            for chunk in r:
                f.write(chunk)


def generate_key(vol):
    return "{0} - Volume {1}.epub".format(vol.manga.name, vol.number)


def make_volume_dir(volume_id):
    v = Volume.objects.get(id=volume_id)
    path = os.path.join("/tmp/Manga", f"{v.manga.id}", v.__str__())
    os.makedirs(path, exist_ok=True)
    return path


def extract_chapters(volume_id):
    v = Volume.objects.get(id=volume_id)
    chapters = v.chapters.all()
    return chapters


def download_chapter(path, chapter_id):
    c = Chapter.objects.get(id=chapter_id)
    urls = extract_images_url(c.source, c.volume.manga.web_source)
    if len(urls) <= 2:
        raise ValueError("Not enough images")
    for index, url in enumerate(urls):
        download(chapter_id, index, path, url)


def download_volume(volume_id):
    path = make_volume_dir(volume_id)
    chapters = extract_chapters(volume_id)
    for chap in chapters:
        download_chapter(path, chap.id)

    delete_corrupt_file(path)
    return path


def generate_manga(path, profile="KV"):
    args = shlex.split(
        "kcc-c2e -m -q -p {1} -f MOBI {2}".format(
            settings.BASE_DIR, profile, shlex.quote(path)
        )
    )
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.communicate()
    print(f"Make {path} successful")
    return "{}.mobi".format(path)


def delete_corrupt_file(path):
    for filename in os.listdir(path):
        try:
            img = Image.open(os.path.join(path, filename))
            img.verify()
        except (IOError, SyntaxError) as e:
            os.remove(os.path.join(path, filename))
            logger.info(
                "Removed corrupted image {}".format(
                    os.path.join(path, filename))
            )

    return path


def upload_and_save(path, volume_id):
    print(path)
    v = Volume.objects.get(id=volume_id)
    with open(path, 'rb') as f:
        v.file.save(f"volume_{v.number}.mobi", File(f))
        v.save()
    shutil.rmtree(path.split(".mobi")[0])
    os.remove(path)
    return v.manga.name


def send_notification(volume_id, email):
    v = Volume.objects.get(id=volume_id)
    send_mail(
        "[Kindlemanga.xyz] {} - Volume {} has been converted".format(
            v.manga.name, v.number
        ),
        "Hello {0}, your manga: {1} - Volume {2} has been converted successful. Please check it at {3}".format(
            email,
            v.manga.name,
            v.number,
            "https://kindlemanga.xyz" + v.manga.get_absolute_url(),
        ),
        os.getenv("GMAIL_EMAIL", "kindlemanga.xyz@gmail.com"),
        [
            email,
        ],
    )
    logger.debug("Send email to {} succeed".format(email))

    if os.getenv("PUSHOVER_ENABLE"):
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_APP_TOKEN"),
                "user": os.getenv("PUSHOVER_USER_KEY"),
                "message": "Convert manga {} - volume {} succeed. User email: {}".format(
                    v.manga.name, v.number, email
                ),
            },
        )


@app.task(name="make_volume")
def make_volume(volume_id, email):
    print("Start make volume {}".format(volume_id))
    path = download_volume(volume_id)
    generated_path = generate_manga(path)
    res = upload_and_save(generated_path, volume_id)
    return res
