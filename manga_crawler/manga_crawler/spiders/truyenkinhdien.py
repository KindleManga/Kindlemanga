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
            restrict_xpaths='//*[@class="next page-number"]')),
        Rule(
            LinkExtractor(
                restrict_xpaths='//*[@class="woocommerce-LoopProduct-link woocommerce-loop-product__link"]'),
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
        chapters = zip(chapter_name, chapter_source)

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
        print(manga.load_item())

        return manga.load_item()


"""
function wait_for_element(splash, css, maxwait)
  -- Wait until a selector matches an element
  -- in the page. Return an error if waited more
  -- than maxwait seconds.
  if maxwait == nil then
      maxwait = 10
  end
  return splash:wait_for_resume(string.format([[
    function main(splash) {
      var selector = '%s';
      var maxwait = %s;
      var end = Date.now() + maxwait*1000;

      function check() {
        if(document.querySelector(selector)) {
          splash.resume('Element found');
        } else if(Date.now() >= end) {
          var err = 'Timeout waiting for element';
          splash.error(err + " " + selector);
        } else {
          setTimeout(check, 200);
        }
      }
      check();
    }
  ]], css, maxwait))
end

function main(splash, args)
  splash:go("https://truyenkinhdien.com/comic/truyen-tranh-biet-doi-linh-cuu-hoa-enen-no-shouboutai-chap-2")
  wait_for_element(splash, ".sgdg-grid-img")
  while splash:select('.sgdg-more-button') do
    local scroll_to = splash:jsfunc("window.scrollTo")
    local get_body_height = splash:jsfunc(
      "function() {return document.body.scrollHeight;}"
    )
    scroll_to(0, get_body_height())
    splash:wait(3)
  end
  return {png=splash:png(), html=splash:html()}
end
"""
