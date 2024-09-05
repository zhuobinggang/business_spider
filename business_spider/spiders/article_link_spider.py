from pathlib import Path

import scrapy

class ArticleLinkSpider(scrapy.Spider):
    name = "article_link"

    def start_requests(self):
        prefix = 'https://www.businessinsider.jp/business/'
        urls = [prefix+str(i) for i in range(60, 100)]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url.split("/")[-1]
        filename = f"./article_links/page-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")