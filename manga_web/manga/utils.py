import logging
import io
import os
import hashlib
import posixpath
from django.core.cache import cache
from retry import retry

try:
    from urllib import unquote

    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit, unquote

from django.conf import settings
import requests
from lxml import html
from fp.fp import FreeProxy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

logger = logging.getLogger(__name__)

s = requests.Session()
IMAGE_EXTS = [".jpg", ".png", ".jpeg"]


class NoImagesFound(Exception):
    pass


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

MANGASEE_HEADERS = {
    "Cookies": "History=%255B%257B%2522IndexName%2522%253A%2522Naruto%2522%252C%2522SeriesName%2522%253A%2522Naruto%2522%252C%2522Chapter%2522%253A%2522100010%2522%252C%2522Page%2522%253A0%252C%2522TimeStamp%2522%253A1697010523%257D%252C%257B%2522IndexName%2522%253A%2522Ore-No-Ie-Ga-Maryoku-Spot-Datta-Ken%2522%252C%2522SeriesName%2522%253A%2522Ore%2520no%2520Ie%2520ga%2520Maryoku%2520Spot%2520datta%2520Ken%2522%252C%2522Chapter%2522%253A%2522101650%2522%252C%2522Page%2522%253A1%252C%2522TimeStamp%2522%253A1696651758%257D%255D; FullPage=yes; PHPSESSID=sgpc4vgd6kgv32uhm9qifmf460",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Host": "mangasee123.com",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}

def fix_url(source, url):
    if source == "truyenkinhdien":
        return url.replace("https://truyenkinhdien.com", "https://webtrainghiem.com")


@retry(tries=5, delay=3, backoff=1.5)
def extract_images_url(url, source):
    """
    Extract image url for a chapter
    """
    if source == "mangaseeonline":
        # r = s.get(
        #     settings.SPLASH_URL,
        #     params={"url": url.replace("-page-1", ""), "wait": 1},
        # )
        # tree = html.fromstring(r.text)
        # return tree.xpath('//*[@id="TopPage"]/descendant::img/@src')
        # html_page = selenium_fetch(url)
        # tree = html.fromstring(html_page)
        # result = tree.xpath('//*[@id="TopPage"]/descendant::img/@src')
        # print(result)
        # return result
        return None
    if source == "nettruyen":
        r = s.get(
            settings.SPLASH_URL, params={"url": url.replace("-page-1", ""), "wait": 1}
        )
        tree = html.fromstring(r.text)
        return tree.xpath('//*[@class="reading-detail box_doc"]/div/img/@src')
    if source == "doctruyen3q":
        r = s.get(settings.SPLASH_URL, params={"url": url, "wait": 1})
        tree = html.fromstring(r.text)
        return tree.xpath('//*[contains(@id, "page_")]/img/@src')
    if source == "truyenkinhdien":
        url = fix_url(source, url)
        r = s.get(
            settings.SPLASH_URL.replace("render.html", "execute"),
            params={"url": url, "lua_source": lua_script, "wait": 1},
        )
        tree = html.fromstring(r.json()["html"])
        result = tree.xpath('//*[@class="entry-content single-page"]/img/@src')
        if not result:
            raise NoImagesFound("No images found")
        return result


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


def get_proxy(source):
    key = f"proxy:{source}"
    proxy = cache.get(key)
    if proxy:
        return proxy
    proxy = FreeProxy(https=True, country_id=["US", "SG", "JP", "CA", "VN"]).get()
    cache.set(key, proxy, 60 * 60 * 10)
    return proxy


def reset_proxy(source):
    cache.delete(f"proxy:{source}")


def calculate_file_hash(file_path):
    # Create an MD5 hash of the file's content
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def remove_duplicate_images(folder_path):
    # Dictionary to store hashes of seen images
    seen_hashes = {}

    # Iterate through files in the folder
    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            # Check if the file is an image (you can add more image file extensions if needed)
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                # Calculate the hash of the image file
                file_hash = calculate_file_hash(file_path)

                # Check if the hash already exists in the dictionary
                if file_hash in seen_hashes:
                    print(f"Removing duplicate: {file_path}")
                    os.remove(file_path)
                else:
                    seen_hashes[file_hash] = file_path


def selenium_fetch(url):
    # Initialize a Chrome webdriver
    options = webdriver.FirefoxOptions()
    options.headless = True
    # disable image load
    options.set_preference("permissions.default.image", 2)
    options.add_argument("--no-sandbox")
    options.add_argument("--mute-audio")
    driver = webdriver.Firefox(
        options=options, service=FirefoxService(GeckoDriverManager().install())
    )
    driver.maximize_window()

    try:
        # Navigate to the specified URL
        driver.get(url)
        # Get the HTML source after scrolling
        html_source = driver.page_source
    finally:
        # Close the browser window
        driver.quit()

    return html_source