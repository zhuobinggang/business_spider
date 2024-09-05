from pathlib import Path

import scrapy


class LocalArticleLinkSpider(scrapy.Spider):
    name = "local_article_link"

    def start_requests(self):
        sample_link = 'file:///home/taku/research/business_spider/business_spider/spiders/article_links/page-2.html'
        urls = [f'file:///home/taku/research/business_spider/business_spider/spiders/article_links/page-{i}.html' for i in range(60, 100)]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def filter_cards(self,response):
        cards = response.css('div.p-cardList-card')
        available_cards = []
        for card in cards:
            if card.css('a.p-label-primeLabelInner::text').get() is not None: # 是prime
                continue
            if '［編集部］' not in ' '.join(card.css('li.p-cardList-cardAuthor::text').getall()): # 是prime
                continue
            available_cards.append(card)
        return available_cards
    
    def links_from_cards(self, cards):
        links = []
        for card in cards:
            links.append(card.css('h1.p-cardList-cardTitle a::attr(href)').get())
        return links

    def links_add_prefix(self, links):
        home = 'https://www.businessinsider.jp'
        return [home+link for link in links]
        
    def get_article_links(self, response):
        return self.links_add_prefix(self.links_from_cards(self.filter_cards(response)))

    def parse(self, response):
        links = self.get_article_links(response)
        page = response.url.split("/")[-1]
        page = page.split('.')[0]
        f = open(f'./article_links_clean/{page}.txt', 'w')
        for link in links:
            f.write(link+'\n')
            self.log(link)
        f.close()