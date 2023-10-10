import logging
import os
import shlex
import shutil
import subprocess
import traceback
from concurrent.futures import ThreadPoolExecutor, wait

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.text import slugify
from django.core.files.base import File
from main.celery import app
from PIL import Image, ImageFile
from retry import retry

from .models import Chapter, Volume
from .utils import (
    extract_images_url,
    url2filename,
    reset_proxy,
    get_proxy,
    remove_duplicate_images,
)

ImageFile.LOAD_TRUNCATED_IMAGES = True

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


class ImageInvalidError(Exception):
    pass


def is_valid_image(path):
    try:
        img = Image.open(path)
        img.verify()
        return True
    except (IOError, SyntaxError) as e:
        return False


@retry(tries=5, delay=2, backoff=1.5)
def download(chapter_id, index, path, url):
    filename = url2filename(url, chapter_id, index)
    logger.debug("Downloading %s", filename)
    if not url.startswith("http"):
        url = "http:" + url

    proxy = get_proxy()
    logger.debug("Using proxy %s", proxy)
    try:
        r = requests.get(url, stream=True)
    except Exception as e:
        logger.error(f"Failed to download {url}")
        reset_proxy()
        raise e
    if r.status_code == 200:
        with open(os.path.join(path, filename), "wb") as f:
            for chunk in r:
                f.write(chunk)
    else:
        logging.debug("Trying with curl")
        cmd = f"curl '{url}' -H 'accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8' --compressed -o {os.path.join(path, filename)}"
        subprocess.call(cmd, shell=True)
    if not is_valid_image(os.path.join(path, filename)):
        reset_proxy()
        raise ImageInvalidError(f"Image {filename} is invalid")
    logger.debug("Downloaded %s", filename)


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
    if not os.path.exists(path):
        os.makedirs(path)
    c = Chapter.objects.get(id=chapter_id)
    urls = extract_images_url(c.source, c.volume.manga.web_source)
    if len(urls) <= 2:
        logging.warning("Chapter %s has only %s images", c.id, len(urls))
        return
    add_watermark(path)
    threads = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for index, url in enumerate(urls):
            threads.append(executor.submit(download, chapter_id, index, path, url))

    wait(threads)


def download_volume(volume_id):
    path = make_volume_dir(volume_id)
    chapters = extract_chapters(volume_id)
    for chap in chapters:
        download_chapter(path, chap.id)

    remove_duplicate_images(path)
    delete_corrupt_file(path)
    return path


def add_watermark(path):
    img = os.path.join(settings.BASE_DIR, "static/image/kindlemanga_cover.png")
    img = Image.open(img)
    img.save(os.path.join(path, "_cover.png"))


def generate_manga(path, volume_id, profile="KPW"):
    vol = Volume.objects.get(id=volume_id)
    logger.info("Start converting %s", vol.title())
    args = shlex.split(
        f"/app/kcc-5.6.3/kcc-c2e.py -m -q -p {profile} -f EPUB -t {shlex.quote(vol.title())} {shlex.quote(path)}"
    )
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.communicate()
    file_path = f"{path}.epub"
    if os.path.getsize(file_path) >> 20 < 4:
        raise ValueError("Converted file size is too small")

    logger.info("Converted %s", vol.title())
    return file_path


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
                "Removed corrupted image {}".format(os.path.join(path, filename))
            )

    return path


def upload_and_save(path, volume_id):
    v = Volume.objects.get(id=volume_id)
    file_name = f"{slugify(v.manga.name).replace('-', '_')}_vol_{v.number}.epub"
    with open(path, "rb") as f:
        v.file.save(file_name, File(f))
        v.save()
    shutil.rmtree(path.split(".epub")[0])
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
