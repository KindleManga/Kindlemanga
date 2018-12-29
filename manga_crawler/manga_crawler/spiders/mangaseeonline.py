# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose
from scrapy.spiders import CrawlSpider, Rule

from manga_crawler.items import MangaCrawlerItem


make_full_url = lambda x: 'http://mangaseeonline.us' + x.replace('-page-1', '')


class MangaseeonlineSpider(CrawlSpider):
    name = 'mangaseeonline'
    allowed_domains = ['mangaseeonline.us']
    start_urls = ['http://mangaseeonline.us/directory/']

    rules = (
        Rule(
            LinkExtractor(
                restrict_xpaths='//*[@class="seriesList chapOnly"]/a',
            ),
            callback='parse_item',
        ),
    )

    def parse_item(self, response):
        manga = ItemLoader(item=MangaCrawlerItem(), response=response)
        manga.add_xpath('name', '//h1[@class="SeriesName"]/text()')
        manga.add_value('source', response.url)
        manga.add_xpath('image_src', '//meta[@property="og:image"]/@content')
        manga.add_xpath('description', '//*[@class="description"]/text()', Join('\n'))

        if 'Complete (Publish)' in manga.get_xpath('//*[@class="PublishStatus"]/text()'):
            manga.add_value('full', True)
        else:
            manga.add_value('full', False)

        chapter_xpath = '//*[@class="list chapter-list"]/a'

        manga.add_value(
            'total_chap',
            manga.get_xpath(
                chapter_xpath + '/span/text()',
                MapCompose(lambda x: re.findall(r'\d+', x))
            )[0]
        )

        chapter_source = manga.get_xpath(chapter_xpath + '/@href', MapCompose(make_full_url))
        chapter_name = manga.get_xpath(chapter_xpath + '/span/text()')
        chapters = zip(chapter_name, chapter_source)
        manga.add_value('chapters', chapters)
        manga.add_value('web_source', 'mangaseeonline')

        return manga.load_item()
