import re

from unidecode import unidecode
from manga_crawler.items import MangaCrawlerItem
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy_splash import SplashRequest
from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.spiders import CrawlSpider, Rule


pattern = r"(\d+(?:\.\d+)?)"


class VlogtruyenSpider(CrawlSpider):
    name = "vlogtruyen"
    allowed_domains = ["vlogtruyen.net"]
    start_urls = ["https://vlogtruyen.net/the-loai/manga"]

    rules = (
        Rule(LinkExtractor(
            restrict_xpaths='//*[@class="pag-next"]'), process_request='splash_request'),
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="load-preview"]'),
            process_request="splash_request",
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
        @url http://splash:8050/render.html?&url=https://vlogtruyen.net/bokutachi-wa-hanshoku-wo-yameta.html&wait=1
        @scrapes name unicode_name source image_src total_chap description chapters web_source full
        """

        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath(
            "unicode_name", '//h1[@class="title-commic-detail"]/text()')
        manga.add_value("name", unidecode(
            manga.get_output_value("unicode_name")[0]))
        manga.add_value("source", response.url)
        manga.add_xpath("image_src", '//meta[@property="og:image"]/@content')
        manga.add_xpath(
            "description", '//*[@class="desc-commic-detail"]/text()', Join("\n")
        )
        chapter_xpath = '//*[@class="ul-list-chaper-detail-commic"]/li/a'
        chapter_source = manga.get_xpath(chapter_xpath + "/@href")
        chapter_name = manga.get_xpath(chapter_xpath + "/h3/text()")
        chapters = zip(chapter_name, chapter_source)

        if "Đã hoàn thành" in manga.get_xpath('//*[@class="manga-status"]/p/text()'):
            manga.add_value("full", True)
        else:
            manga.add_value("full", False)

        manga.add_value(
            "total_chap",
            manga.get_xpath(
                '//*[@class="ul-list-chaper-detail-commic"]/li[1]/a/h3/text()',
                MapCompose(lambda x: re.findall(r"(\d+(?:\.\d+)?)", x)),
                TakeFirst(),
            ),
        )
        manga.add_value("chapters", chapters)
        manga.add_value("web_source", "vlogtruyen")

        return manga.load_item()
