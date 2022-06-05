import logging
import os
import sys

import django

# Django settings
sys.path.append("/home/tu/KindleManga/manga_web/")  # Path to Django project
os.environ["DJANGO_SETTINGS_MODULE"] = "main.settings"

django.setup()


import shutil

import boto3
from django.conf import settings
from get_fshare import FSAPI
from manga.models import Volume

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

logger = logging.getLogger("S3 to Fshare")
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(fmt)

logger.addHandler(handler)


bot = FSAPI(settings.FSHARE_EMAIL, settings.FSHARE_PASSWORD)
bot.login()


def get_filename(url):
    name = url.split("kindle-manga/")[1]
    logger.debug("File name: %s" % name)
    return name


def download(s3, url):
    filename = get_filename(url)
    path = os.path.join("/tmp", filename)
    s3.Bucket("kindle-manga").download_file(filename, path)
    logger.debug("File path: %s" % path)
    return path


def upload(path):
    try:
        result = bot.upload(path, "/KindleManga")
        if "error" in result:
            logger.error(result)
            upload(path)
        else:
            logger.debug(result)
            link = result.get("url")
            logger.debug(link)
            os.remove(path)
            return link
    except Exception as e:
        logger.error(e)


def main():
    s3 = boto3.resource("s3")
    for v in Volume.objects.exclude(
        download_link__isnull=True, fshare_link__isnull=True
    ):
        path = download(s3, v.download_link)
        link = upload(path)
        v.fshare_link = link
        v.save()
        logger.debug("Move {} succeed. ID: {}".format(v.__str__(), v.id))


if __name__ == "__main__":
    main()
