# https://truyenkinhdien.com/

import re
from unidecode import unidecode
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.spiders import CrawlSpider, Rule


class TruyenKinhDienSpider(CrawlSpider):
    name = "tkd"
    allowed_domains = ["truyenkinhdien.com"]
    start_urls = ["https://truyenkinhdien.com/danh-muc/truyen-tranh"]

    rules = (
        Rule(LinkExtractor(
            restrict_xpaths='//*[@class="page-numbers nav-pagination links text-center"]/li'),
        ),
        Rule(
            LinkExtractor(
                restrict_xpaths='//*[@class="title-wrapper"]',
            ),
            callback="parse_item",
        ),
    )

    def parse_item(self, response):
        """
        @url https://truyenkinhdien.com/truyen-tranh/death-note-quyen-so-thien-menh-tu-ky
        @scrapes name source image_src total_chap description chapters web_source full unicode_name
        """
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_value("web_source", "truyenkinhdien")
        manga.add_xpath(
            "unicode_name", '//h1[@class="product-title product_title entry-title"]/text()',
            MapCompose(lambda x: x.strip())
        )
        manga.add_value("name", unidecode(
            manga.get_output_value("unicode_name")[0]))
        manga.add_value("source", response.url)
        manga.add_xpath(
            "image_src", '//*[@class="wp-post-image skip-lazy"]/@src')
        manga.add_xpath(
            "description", '//*[@id="tab-description"]/p//text()',
            Join("")
        )
        chapter_xpath = '//*[@class="comic-archive-list-wrap"]/div/span/a'
        chapter_source = manga.get_xpath(chapter_xpath + "/@href")
        chapter_name = manga.get_xpath(chapter_xpath + "/text()")
        chapters = zip(reversed(chapter_name), reversed(chapter_source))

        if "Full" in manga.get_xpath('//*[@class="tag-groups-label"]//text()'):
            manga.add_value("full", True)
        else:
            manga.add_value("full", False)

        manga.add_value(
            "total_chap",
            manga.get_xpath(
                '//*[@class="cc"]/li[2]/span/text()',
                MapCompose(lambda x: re.findall(r"(\d+(?:\.\d+)?)", x)),
                MapCompose(float),
                MapCompose(int),
                TakeFirst(),
            ),
        )

        manga.add_value("chapters", chapters)
        print(manga.get_output_value("unicode_name"))

        return manga.load_item()
