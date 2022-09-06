import logging
import os
import shlex
import shutil
import subprocess
import traceback

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.text import slugify
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
    logger.debug("downloading %s", filename)
    if not url.startswith("http"):
        url = "http:" + url
    try:
        r = requests.get(url, stream=True)
    except Exception as e:
        print(f"Failed to download {url}")
        return
    if r.status_code == 200:
        with open(os.path.join(path, filename), "wb") as f:
            for chunk in r:
                f.write(chunk)
    else:
        r = requests.get(settings.SPLASH_URL, params={
                         'url': url, 'wait': 1}, stream=True)
        if r.status_code == 200:
            with open(os.path.join(path, filename), "wb") as f:
                for chunk in r:
                    f.write(chunk)


def generate_key(vol):
    return "{0} - Volume {1}.mobi".format(vol.manga.name, vol.number)


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
    print(f"Downloading {c.name}")
    urls = extract_images_url(c.source, c.volume.manga.web_source)
    if len(urls) <= 2:
        return
    for index, url in enumerate(urls):
        download(chapter_id, index, path, url)


def download_volume(volume_id):
    path = make_volume_dir(volume_id)
    chapters = extract_chapters(volume_id)
    for chap in chapters:
        download_chapter(path, chap.id)

    delete_corrupt_file(path)
    return path


def generate_manga(path, volume_id, profile="KPW"):
    vol = Volume.objects.get(id=volume_id)
    args = shlex.split(
        f"kcc-c2e -m -q -p {profile} -f MOBI -t {shlex.quote(vol.title())} {shlex.quote(path)}"
    )
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.communicate()
    file_path = f"{path}.mobi"
    if os.path.getsize(file_path) >> 20 < 4:
        raise ValueError("Converted file size is too small")

    print(f"Make {file_path} successful")
    return "{}.mobi".format(path)


def delete_corrupt_file(path):
    for filename in os.listdir(path):
        try:
            img = Image.open(os.path.join(path, filename))
            img.verify()
            width, height = img.size
            if height < 500:
                os.remove(os.path.join(path, filename))
        except (IOError, SyntaxError) as e:
            os.remove(os.path.join(path, filename))
            logger.info(
                "Removed corrupted image {}".format(
                    os.path.join(path, filename))
            )

    return path


def upload_and_save(path, volume_id):
    v = Volume.objects.get(id=volume_id)
    file_name = f"{slugify(v.manga.name).replace('-', '_')}_vol_{v.number}.mobi"
    with open(path, 'rb') as f:
        v.file.save(file_name, File(f))
        v.save()
    shutil.rmtree(path.split(".mobi")[0])
    os.remove(path)
    return v.manga.name


@app.task(name="make_volume")
def make_volume(volume_id):
    vol = Volume.objects.get(id=volume_id)
    if vol.converting:
        print(f"{vol.manga.name} volume {vol.number} is converting")
        return
    vol.converting = True
    vol.save()
    print(f"Start converting {vol.manga.name} volume {vol.number}")
    try:
        path = download_volume(volume_id)
        generated_path = generate_manga(path, volume_id)
        res = upload_and_save(generated_path, volume_id)
        vol = Volume.objects.get(id=volume_id)
        vol.converting = False
        vol.save()
        return res
    except Exception as e:
        traceback.print_exc()
        vol = Volume.objects.get(id=volume_id)
        vol.converting = False
        vol.save()
        return False
