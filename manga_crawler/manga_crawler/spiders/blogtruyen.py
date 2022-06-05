# -*- coding: utf-8 -*-
import re

import scrapy
from manga_crawler.items import MangaCrawlerItem
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose

mc = lambda x: "http://blogtruyen.com" + x


class BlogtruyenSpider(scrapy.Spider):
    name = "blogtruyen"
    allowed_domains = ["blogtruyen.com"]
    start_urls = [
        "http://blogtruyen.com/ajax/Search/AjaxLoadListManga?key=tatca&orderBy=3&p={}"
    ]
    page_numb = 653

    def start_requests(self):
        for url in self.start_urls:
            for i in range(self.page_numb):
                request = Request(url.format(i))
                yield request

    def parse(self, response):
        url_selector = response.xpath('//*[@class="tiptip fs-12 ellipsis"]/a/@href')

        for url in url_selector.extract():
            rq = Request(mc(url), callback=self.parse_item)
            yield rq

    def parse_item(self, response):
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)

        manga.add_xpath(
            "name", "//title/text()", MapCompose(lambda x: x.split(" | ")[0], str.strip)
        )
        manga.add_value("source", response.url)
        manga.add_xpath("image_src", '//*[@class="thumbnail"]/img/@src')
        manga.add_xpath(
            "description",
            '//*[@class="content"]//text()',
            MapCompose(str.strip),
            Join("\n"),
            MapCompose(str.strip),
        )
        manga.add_value(
            "total_chap",
            max(
                [
                    int(i)
                    for i in manga.get_xpath(
                        '//*[@id="list-chapters"]/p/span/a/text()',
                        MapCompose(lambda x: re.findall(r"\d+", x)),
                    )
                ]
            ),
        )

        get_chapter_source = manga.get_xpath(
            '//*[@id="list-chapters"]/p/span/a/@href', MapCompose(mc)
        )
        chapter_source = [
            chap for chap in get_chapter_source if "mediafire" not in chap
        ]
        chapter_name = manga.get_xpath('//*[@id="list-chapters"]/p/span/a/text()')
        chapters = zip(chapter_name, chapter_source)

        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "blogtruyen")

        if "Đã hoàn thành" in manga.get_xpath('//*[@class="description"]//text()'):
            manga.add_value("full", True)
        else:
            manga.add_value("full", False)

        return manga.load_item()
