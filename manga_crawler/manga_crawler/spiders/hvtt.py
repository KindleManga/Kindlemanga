# -*- coding: utf-8 -*-
import re
import scrapy

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join, MapCompose
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from manga_crawler.items import MangaCrawlerItem


class HvttSpider(CrawlSpider):
    name = 'hvtt'
    allowed_domains = ['hocvientruyentranh.com']
    start_urls = ['http://hocvientruyentranh.com/manga/all?filter_type=view']

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//*[@rel="next"]')),
        Rule(
            LinkExtractor(restrict_xpaths='//*[@class="ajax-call"]/..'),
            callback='parse_item',
        ),
    )

    def parse_item(self, response):
        """
        @url http://hocvientruyentranh.com/manga/2/shokugeki-no-souma-
        @returns items 1
        @scrapes name source total_chap chapters description
        """
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)

        manga.add_xpath('name', '//h3[@class="__name"]/text()', MapCompose(str.strip))
        manga.add_value('source', response.url)
        manga.add_xpath('image_src', '//*[@class="__image"]/img/@src')
        manga.add_xpath('description', '//*[@class="__description"]//p/text()', Join('\n'))
        manga.add_value(
            'total_chap',
            max(
                [int(i) for i in
                    manga.get_xpath(
                        '//*[@class="table table-hover"]/tbody//tr//td//a//text()',
                        MapCompose(lambda x: re.findall(r'\d+', x)))]
            )
        )

        chapter_source = manga.get_xpath('//*[@class="table table-hover"]/tbody//tr//td//a/@href')
        chapter_name = manga.get_xpath('//*[@class="table table-hover"]/tbody//tr//td//a//text()')
        chapters = zip(chapter_name, chapter_source)

        manga.add_value('chapters', chapters)

        return manga.load_item()
