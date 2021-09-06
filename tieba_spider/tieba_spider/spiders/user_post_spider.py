import json
import urllib

import pandas as pd
import scrapy
from pydispatch import dispatcher
from scrapy import signals
from scrapy.selector import Selector

import tieba_spider


class UserPostSpider(scrapy.Spider):
    name = 'user_post_spider'
    start_urls = [
        'https://tieba.baidu.com/home/main?un=SVEN3777&red_tag=p3039495051&referer=tieba.baidu.com']

    def __init__(self, config=None, *args, **kwargsf):
        self.floor = 12
        tieba_spider.csv_file_name = f'user_L{self.floor}'
        self.user_pd = pd.read_csv('{0}{1}.csv'.format(tieba_spider.data_path, f'user_L{self.floor}'),
                                   encoding='utf_8_sig', engine='python')
        self.user_pd.drop_duplicates(inplace=True)
        self.data = pd.DataFrame(columns=['author_user_name', 'post_title', 'url', 'bar_name', 'forum_category'])
        self.data['forum_category'] = None
        # 将信号与函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    # 爬虫结束时执行的函数
    def spider_closed(self, spider):
        self.data.to_csv('{0}{1}.csv'.format(tieba_spider.data_path, f'user_L{self.floor}_post'),
                         encoding='utf_8_sig', index=False)

    def parse(self, response):
        # 爬取用户关注贴吧的信息  移动端
        self.headers = {
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'}

        for index, rows in self.user_pd.iterrows():
            yield scrapy.Request(
                url=('https://tieba.baidu.com/home/main?un=%s' % urllib.parse.quote(rows['author_user_name'])),
                headers=self.headers,
                meta={"author_user_name": rows['author_user_name']},
                callback=self.parse_user_post,
            )

    def parse_user_post(self, response):
        author_user_name = response.meta['author_user_name']
        #  屏蔽动态的 使用特殊值 -1 来表示
        for li in response.xpath("//ul[@id='home_thread_list_list']/li"):
            row = [author_user_name,
                   li.xpath(".//span[@class='post_list_item_title']/text()").get(),
                   li.xpath(".//a[@class='list_item_link']/@href").get(),
                   li.xpath(".//span[@class='post_list_item_info_forum']/text()").get(),
                   None
                   ]
            self.data.loc[self.data.shape[0]] = row

        # 需要解析ajax的json内容
        try:
            ajax_url = ('https://tieba.baidu.com/home/post?un=%s' % urllib.parse.quote(author_user_name) +
                        '&is_ajax=1&lp=home_main_concern_more&pn=2')
            # 爬取用户关注贴吧的信息  移动端
            yield scrapy.Request(
                ajax_url,
                headers=self.headers,
                callback=self.parse_post_ajax,
                meta={"author_user_name": author_user_name},
                dont_filter=True,
            )
        except BaseException:
            pass

    # 抓取ajax加载的信息
    def parse_post_ajax(self, response):
        author_user_name = response.meta['author_user_name']
        data = json.loads(response.body)
        code = data['data']['content']

        for li in Selector(text=code).xpath("//li"):
            row = [author_user_name,
                   li.xpath(".//span[@class='post_list_item_title']/text()").get(),
                   li.xpath(".//a[@class='list_item_link']/@href").get(),
                   li.xpath(".//span[@class='post_list_item_info_forum']/text()").get(),
                   None
                   ]
            self.data.loc[self.data.shape[0]] = row

        has_more = data['data']['page']['has_more']  # int
        if has_more:
            page = int(response.url.split('pn=')[1]) + 1
            next_url = response.url.split('pn=')[0] + 'pn=' + repr(page)
            yield scrapy.Request(
                next_url,
                headers=self.headers,
                callback=self.parse_post_ajax,
                meta={"author_user_name": author_user_name},
                dont_filter=True,
            )


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl('user_post_spider')
    process.start()
