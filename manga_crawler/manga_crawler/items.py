# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class MangaCrawlerItem(scrapy.Item):
    name = scrapy.Field()
    source = scrapy.Field()
    total_chap = scrapy.Field()
    image_src = scrapy.Field()
    chapters = scrapy.Field()
