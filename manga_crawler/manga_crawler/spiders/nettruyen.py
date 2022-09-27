# -*- coding: utf-8 -*-
import re
from unidecode import unidecode
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.spiders import CrawlSpider, Rule


class NettruyenSpider(CrawlSpider):
    name = "nettruyen"
    allowed_domains = ["www.nettruyenco.com"]
    start_urls = [
        "http://splash:8050/render.html?&url=http://www.nettruyenco.com/tim-truyen/manga-112"
    ]

    rules = (
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="next-page"]'),
            process_request="splash_request",
        ),
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="jtip"]'),
            process_request="splash_request",
        ),
    )

    def splash_request(self, request, *args, **kwargs):
        if "?page=" in request.url:
            return SplashRequest(
                request.url,
                endpoint="render.html",
                args={"wait": 1},
            )
        else:
            return SplashRequest(
                request.url,
                callback=self.parse_item,
                endpoint="render.html",
                args={"wait": 1},
            )

    def parse_item(self, response):
        """
        @url http://splash:8050/render.html?&url=http://www.nettruyenco.com/truyen-tranh/boyfriend-17550&wait=1
        @scrapes name source image_src total_chap description chapters web_source full
        """
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath("unicode_name", '//h1[@class="title-detail"]/text()')
        manga.add_value("name", unidecode(manga.get_output_value("unicode_name")[0]))
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
                    MapCompose(float),
                    MapCompose(int),
                    TakeFirst(),
                ),
            )

        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "nettruyen")
        print(manga.load_item())

        return manga.load_item()
