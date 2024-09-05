from pathlib import Path

import scrapy

class SingleHtmlSpider(scrapy.Spider):
    name = "single_html"

    def start_requests(self):
        for page_index in range(60, 100):
            with open(f'article_links_clean/page-{page_index}.txt', 'r') as f:
                links = f.read().splitlines()
            for link in links:
                yield scrapy.Request(url=link, callback=self.parse, meta={'page_index': page_index})

    def parse(self, response):
        page = response.url.split("/")[-1]
        filename = f"./article_htmls/page-{response.meta['page_index']}-{page}.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")