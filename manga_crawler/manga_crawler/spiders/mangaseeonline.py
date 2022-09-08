# -*- coding: utf-8 -*-
import feedparser
import re
import requests
from unidecode import unidecode

import scrapy
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose
from scrapy.spiders import CrawlSpider, Rule

BASE_URL = "https://mangasee123.com"


def make_full_url(x):
    return BASE_URL + x.replace("-page-1", "")


class MangaseeonlineSpider(CrawlSpider):
    name = "mangaseeonline"
    allowed_domains = ["mangasee123.com"]
    start_urls = ["https://mangasee123.com/_search.php"]

    def __init__(self, *a, **kw):
        self.data = requests.get(self.start_urls[0]).json()

    def start_requests(self):
        for item in self.data:
            request = scrapy.Request(
                f"{BASE_URL}/manga/{item['i']}", callback=self.parse_item
            )
            request.meta["item"] = item
            yield request

    def parse_item(self, response):
        """
        @url https://mangasee123.com/manga/Kingdom
        @scrapes name source image_src total_chap description chapters web_source full
        """
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath(
            "unicode_name", "//div[@class='container MainContainer']//li[1]/h1/text()"
        )
        manga.add_value("name", unidecode(manga.get_output_value("unicode_name")[0]))
        manga.add_value("source", response.url)
        manga.add_xpath("image_src", '//meta[@property="og:image"]/@content')
        manga.add_xpath(
            "description", "//div[@class='top-5 Content']/text()", Join("\n")
        )

        if "Complete (Publish)" in manga.get_xpath(
            '//*[@class="PublishStatus"]/text()'
        ):
            manga.add_value("full", True)
        else:
            manga.add_value("full", False)

        rss = manga.get_xpath("//a[normalize-space()='RSS Feed']/@href")
        rss_url = BASE_URL + rss[0]

        feed = feedparser.parse(rss_url, agent="Mozilla/5.0")

        manga.add_value(
            "total_chap",
            re.findall(r"\d+", feed["entries"][0]["title"])[0],
        )

        chapters = [(i["title"], i["link"]) for i in feed["entries"]]
        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "mangaseeonline")

        return manga.load_item()
