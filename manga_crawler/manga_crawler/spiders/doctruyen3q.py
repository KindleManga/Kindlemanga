import re
from unidecode import unidecode
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.spiders import CrawlSpider, Rule


class Truyen3QSpider(CrawlSpider):
    name = "3q"
    allowed_domains = ["doctruyen3q.info"]
    start_urls = ["https://doctruyen3q.info/tim-truyen/manga"]

    rules = (
        Rule(LinkExtractor(
            restrict_xpaths='//*[@rel="next"]')),
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="title-manga"]'),
            callback="parse_item",
        ),
    )

    def splash_request(self, request, *args, **kwargs):
        if "?page=" in request.url:
            return SplashRequest(
                request.url,
                endpoint='render.html',
                args={'wait': 1},
            )
        else:
            return SplashRequest(
                request.url,
                callback=self.parse_item,
                endpoint='render.html',
                args={'wait': 1},
            )

    def parse_item(self, response):
        """
        @url https://doctruyen3q.info/truyen-tranh/hoi-sinh-the-gioi/660
        @scrapes name source image_src total_chap description chapters web_source full unicode_name
        """
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath("unicode_name", '//h1[@class="title-manga"]/text()')
        manga.add_value("name", unidecode(
            manga.get_output_value("unicode_name")[0]))
        manga.add_value("source", response.url)
        manga.add_xpath(
            "image_src", '//*[@class="image-comic"]/@src')
        manga.add_xpath(
            "description", '//*[@class="detail-summary"]/text()'
        )
        chapter_xpath = '//*[@id="list-chapter-dt"]/nav/ul/li/div[1]/a'
        chapter_source = manga.get_xpath(chapter_xpath + "/@href")
        chapter_name = manga.get_xpath(chapter_xpath + "/text()")
        chapters = zip(chapter_name, chapter_source)

        if "Đã hoàn thành" in manga.get_xpath('//*[@class="status row"]//text()'):
            manga.add_value("full", True)
        else:
            manga.add_value("full", False)

        manga.add_value(
            "total_chap",
            manga.get_xpath(
                '//*[@id="list-chapter-dt"]/nav/ul/li[1]/div[1]/a/text()',
                MapCompose(lambda x: re.findall(r"(\d+(?:\.\d+)?)", x)),
                TakeFirst(),
            ),
        )

        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "doctruyen3q")
        print(manga.load_item())

        return manga.load_item()
