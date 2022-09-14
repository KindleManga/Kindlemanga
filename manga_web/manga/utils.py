import logging
import io
import os
import posixpath

try:
    from urllib import unquote

    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit, unquote

from django.conf import settings
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
                if image_url != url:
                    return "{}_{}_{}.jpg".format(
                        "{:0>10}".format(chapter_id),
                        "{:0>6}".format(index),
                        url2filename(image_url),
                    )
                else:
                    return "{}_{}.jpg".format(
                        "{:0>10}".format(chapter_id), "{:0>6}".format(index)
                    )
            except IndexError:
                logger.error("No image url found in url")
        logger.error("This file name is not image")
    return "{}_{}_{}".format(chapter_id, index, basename)


lua_script = r"""
function wait_for_element(splash, css, maxwait)
  -- Wait until a selector matches an element
  -- in the page. Return an error if waited more
  -- than maxwait seconds.
  if maxwait == nil then
      maxwait = 10
  end
  return splash:wait_for_resume(string.format([[
    function main(splash) {
      var selector = '%s';
      var maxwait = %s;
      var end = Date.now() + maxwait*1000;

      function check() {
        if(document.querySelector(selector)) {
          splash.resume('Element found');
        } else if(Date.now() >= end) {
          var err = 'Timeout waiting for element';
          splash.error(err + " " + selector);
        } else {
          setTimeout(check, 200);
        }
      }
      check();
    }
  ]], css, maxwait))
end

function main(splash, args)
  splash:go(args.url)
  wait_for_element(splash, ".sgdg-grid-img")
  while splash:select('.sgdg-more-button') do
    local scroll_to = splash:jsfunc("window.scrollTo")
    local get_body_height = splash:jsfunc(
      "function() {return document.body.scrollHeight;}"
    )
    scroll_to(0, get_body_height())
    splash:wait(3)
  end
  return {html=splash:html()}
end
"""


def extract_images_url(url, source):
    """
    Extract image url for a chapter
    """
    if source == "mangaseeonline":
        r = s.get(
            settings.SPLASH_URL, params={
                "url": url.replace("-page-1", ""), "wait": 1}
        )
        tree = html.fromstring(r.text)
        return tree.xpath('//*[@id="TopPage"]/descendant::img/@src')
    if source == "nettruyen":
        r = s.get(
            settings.SPLASH_URL, params={
                "url": url.replace("-page-1", ""), "wait": 1}
        )
        tree = html.fromstring(r.text)
        return tree.xpath('//*[@class="reading-detail box_doc"]/div/img/@src')
    if source == "doctruyen3q":
        r = s.get(
            settings.SPLASH_URL, params={"url": url, "wait": 1}
        )
        tree = html.fromstring(r.text)
        return tree.xpath('//*[contains(@id, "page_")]/img/@src')
    if source == "truyenkinhdien":
        r = s.get(
            settings.SPLASH_URL.replace("render.html", "execute"),
            params={"url": url, "lua_source": lua_script, "wait": 1},
        )
        tree = html.fromstring(r.json()["html"])
        return tree.xpath(
            '//*[@class="sgdg-gallery"]/a[not(contains(@style,"display:none"))]/img/@src'
        )


def image_to_bytesio(url):
    """
    Return bytesio of image
    """
    if not url.startswith("http"):
        url = "http:" + url
    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        raise (Exception("Error getting image"))
    return io.BytesIO(resp.content)
