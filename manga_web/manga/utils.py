import logging
import os
import posixpath

try:
    from urllib import unquote

    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit, unquote

import requests
from lxml import html

logger = logging.getLogger(__name__)

s = requests.Session()
IMAGE_EXTS = [".jpg", ".png", ".jpeg"]


def url2filename(url, chapter_id=None, index=None):
    """Return basename corresponding to url.
    >>> print(url2filename('http://example.com/path/to/file%C3%80?opt=1'))
    fileÀ
    >>> print(url2filename('http://example.com/slash%2fname')) # '/' in name
    Traceback (most recent call last):
    ...
    ValueError
    """
    urlpath = urlsplit(url).path
    basename = posixpath.basename(unquote(urlpath))
    if (
        os.path.basename(basename) != basename
        or unquote(posixpath.basename(urlpath)) != basename
    ):
        raise ValueError  # reject '%2f' or 'dir%5Cbasename.ext' on Windows

    if not any([basename.lower().endswith(i) for i in IMAGE_EXTS]):
        if url.find("googleusercontent.com") != -1:
            try:
                new_url = unquote(url)
                image_url = new_url.split("url=")[-1]
                return "{}_{}_{}".format(chapter_id, index, url2filename(image_url))
            except IndexError:
                logger.error("No image url found in url")
        logger.error("This file name is not image")
    return "{}_{}_{}".format(chapter_id, index, basename)


# def extract_images_url(url):
#     """
#     Extract image url for a chapter in HocVienTruyenTranh
#     """
#     r = s.get(url)
#     tree = html.fromstring(r.text)
#     return tree.xpath('//div[@class="manga-container"]/img/@src')


def extract_images_url(url, source):
    """
    Extract image url for a chapter
    """
    r = s.get(url)
    tree = html.fromstring(r.text)
    if source == "blogtruyen":
        return tree.xpath('//*[@id="content"]/img/@src')
    elif source == "nettruyen":
        return tree.xpath('//*[@class="reading-detail box_doc"]/div/img/@src')
    elif source == "image-container-manga":
        return tree.xpath('//*[@class="image-container-manga"]/div/img/@src')
