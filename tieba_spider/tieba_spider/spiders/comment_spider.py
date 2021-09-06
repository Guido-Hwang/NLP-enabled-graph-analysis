# -- coding: UTF-8 --
import json
import os
import re
import urllib
import time
import pandas as pd
import scrapy
from scrapy import Selector

import tieba_spider
from scrapy import signals
from pydispatch import dispatcher


# 爬取用户的关注信息
class CommentSpider(scrapy.Spider):
    '''
    使用post_classify 作为输入
    '''
    name = 'comment_spider'
    start_urls = ['https://tieba.baidu.com/p/6495547652']  # 296 回帖的帖子
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # 'tieba_spider.middlewares.TiebaSpiderDownloaderMiddleware': 542,
            # 'tieba_spider.middlewares.ProcessAllExceptionMiddleware': 543,
        }
    }

    def __init__(self, config=None, *args, **kwargsf):
        self.floor = 11
        tieba_spider.csv_file_name = f'user_L{self.floor}_post_comment'

        self.post_pd = pd.read_csv(f'{tieba_spider.data_path}user_L{self.floor}_post_filter.csv',
                                   encoding='utf_8_sig')
        self.data = pd.DataFrame(columns=['author_user_name', 'post_id', 'reply2user', 'content', 'date'])
        # 将信号与函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    # 爬虫结束时执行的函数
    def spider_closed(self, spider):
        self.data.to_csv(f"{tieba_spider.data_path}{tieba_spider.csv_file_name}.csv",
                         encoding='utf_8_sig', index=False)

    def start_requests(self):
        # 携带cookie登录
        self.cookies = 'BIDUPSID=45FB8DA09A914E629390863C57F0DC4B; PSTM=1559219844; TIEBAUID=c9d81907c343f58656236b9c; TIEBA_USERTYPE=771c50dd5a2a1babb2474f72; bdshare_firstime=1559460699558; IS_NEW_USER=c1fb106822622ad8692c2bf4; CLIENTWIDTH=400; CLIENTHEIGHT=922; Hm_lvt_7d6994d7e4201dd18472dd1ef27e6217=1562980079,1563758359,1563949310,1564367330; Hm_lvt_287705c8d9e2073d13275b18dbd746dc=1569076393,1569076433,1569115706,1569325731; BAIDUID=9DD291A3D39F6F5B13BA34CC66477BED:FG=1; H_WISE_SIDS=138596_139454_139405_128064_135847_141003_125695_139148_138470_140853_141440_139193_133995_138878_137978_140174_131247_132552_137745_138165_138883_140259_141367_140631_140202_139296_138585_139174_139625_140113_136196_140591_140578_133847_140793_134047_137817_139232_140311_140968_136537_139575_110085_140324_127969_140957_140593_140420_139885_140996_139409_128196_138313_138425_141193_138942_139676_141190_140597_140962; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; SEENKW=%E6%B8%B8%E6%88%8F%23%E6%96%B0%E5%9E%8B%E5%86%A0%E7%8A%B6%E7%97%85%E6%AF%92%23c%E8%AF%AD%E8%A8%80%23%E4%B8%89%E5%9B%BD%E6%9D%80%23%E5%85%AD%E5%B0%8F%E9%BE%84%E7%AB%A5%23%E4%B8%9C%E6%96%B9%E9%AA%91%E7%A0%8D; SET_PB_IMAGE_WIDTH=312.8; BDUSS=VpCV0tJNFlDUE53NmRXREoybDR5SjhLcU93QU1wTkViOVdMUE55TVBEN2JpSFZlSVFBQUFBJCQAAAAAAAAAAAEAAAA3T50bMTY2OTEzODMwMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANv7TV7b-01eW; STOKEN=8a991e06ca18e97b62d0172d2189b31872260142cf126429e18a0f2a812a0860; 463294263_FRSVideoUploadTip=1; wise_device=0; delPer=0; PSINO=6; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1582711064,1582725071,1582763623,1582763757; H_PS_PSSID=30747_1450_21126_30789_30907_30823_26350; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1582776985'
        self.cookies = {i.split("=")[0]: i.split("=")[1] for i in self.cookies.split(";")}  # cookies 切割
        self.headers = { 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}

        yield scrapy.Request(
            self.start_urls[0],
            callback=self.parse,
            headers=self.headers,
            cookies=self.cookies
        )

    def parse(self, response):
        # 爬取帖子的所有评论
        for index, row in self.post_pd.iterrows():
            try:
                yield scrapy.Request(
                    'https://tieba.baidu.com' + row['url'],
                    meta={"author_user_name": row['author_user_name'], "post_id": row['post_id']},
                    callback=self.parse_floor_comment,
                    headers=self.headers,
                    cookies=self.cookies
                )
            except BaseException as e:
                print(e)

    def parse_floor_comment(self, response):
        # print(response.text)
        try:
            for sel in response.xpath(
                    '//div[contains(@class, "l_post j_l_post l_post_bright  ") or contains(@class, "l_post j_l_post l_post_bright noborder ") ]'):  # 获取帖子信息
                data = json.loads(sel.xpath('@data-field').extract_first())

                author_user_name = data['author']['user_name']
                post_id = response.meta['post_id']
                reply2user = response.meta['author_user_name']  # 第一个发帖的人
                content = sel.xpath(
                    './/div[contains(@class, "d_post_content j_d_post_content  clearfix") ]/text()').get()
                date = data['content']['date']
                self.data.loc[self.data.shape[0]] = [author_user_name, post_id, reply2user, content, date]

            # 自动翻页
            next_url = response.xpath("//a[contains(text(),'下一页')]/@href").get()
            if next_url is not None:
                next_url = urllib.parse.urljoin(response.url, next_url)
                yield scrapy.Request(
                    next_url,
                    callback=self.parse_floor_comment,
                    meta={"author_user_name": reply2user, "post_id": post_id},
                    headers=self.headers,
                    cookies=self.cookies,
                    dont_filter=True  # 防止过滤，不然进入不了执行函数
                )
        except BaseException as error:
            print(error)

    def parse_double_deck(self, response):
        '''
        # 爬取楼中楼需要翻页的评论
        :param response:
        :return:
        '''
        print(response.text)
        names = Selector(text=response.text).xpath("").extract()
        # names = Selector(text=datas).xpath("//div[contains(@class,'jDesc')]/a/text()").extract()


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl('comment_spider')
    process.start()
