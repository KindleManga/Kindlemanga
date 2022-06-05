# -*- coding: utf-8 -*-
import re

import scrapy
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, TakeFirst
from scrapy.spiders import CrawlSpider, Rule


class NettruyenSpider(CrawlSpider):
    name = "nettruyen"
    allowed_domains = ["www.nettruyen.com"]
    start_urls = ["http://www.nettruyen.com/tim-truyen?status=-1&sort=10"]

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//*[@class="next-page"]')),
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="jtip"]'),
            callback="parse_item",
        ),
    )

    def parse_item(self, response):
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath("name", '//h1[@class="title-detail"]/text()')
        manga.add_value("source", response.url)
        manga.add_xpath("image_src", '//*[@class="col-xs-4 col-image"]/img/@src')
        manga.add_xpath(
            "description", '//*[@class="detail-content"]/p//text()', Join("\n")
        )
        chapter_xpath = '//*[@id="nt_listchapter"]/nav/ul/li[not(contains (@class, "row heading"))]/div[1]/a'
        chapter_source = manga.get_xpath(chapter_xpath + "/@href")
        chapter_name = manga.get_xpath(chapter_xpath + "/text()")
        chapters = zip(chapter_name, chapter_source)

        if "Hoàn thành" in manga.get_xpath('//*[@class="status row"]/p[2]/text()'):
            manga.add_value("full", True)
            manga.add_value(
                "total_chap",
                manga.get_xpath(
                    chapter_xpath + "/text()",
                    MapCompose(lambda x: re.findall(r"\d+", x)),
                    MapCompose(int),
                )[0],
            )
        else:
            manga.add_value("full", False)
            manga.add_value(
                "total_chap",
                manga.get_xpath(
                    "//title/text()",
                    MapCompose(lambda x: re.findall(r" Chapter \d+| Chap \d+", x)),
                    MapCompose(lambda x: re.findall(r"\d+", x)),
                    MapCompose(int),
                    TakeFirst(),
                ),
            )

        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "nettruyen")

        return manga.load_item()
