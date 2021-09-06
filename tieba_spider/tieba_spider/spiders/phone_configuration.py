# -*- coding: utf-8 -*-
import json
import re
import pandas as pd

import scrapy
# from scrapy.xlib.pydispatch import dispatcher
from pydispatch import dispatcher
from scrapy import signals


class PhoneConfigurationSpider(scrapy.Spider):
    '''
    获取手机型号
    '''
    name = 'phone_configuration'
    start_urls = ['http://detail.zol.com.cn/cell_phone_index/subcate57_list_1.html']

    def __init__(self):
        # 携带cookie登录
        self.cookies = 'BAIDUID=45FB8DA09A914E629390863C57F0DC4B:FG=1; BIDUPSID=45FB8DA09A914E629390863C57F0DC4B; PSTM=1559219844; TIEBAUID=c9d81907c343f58656236b9c; TIEBA_USERTYPE=771c50dd5a2a1babb2474f72; bdshare_firstime=1559460699558; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; IS_NEW_USER=c1fb106822622ad8692c2bf4; CLIENTWIDTH=400; CLIENTHEIGHT=922; H_WISE_SIDS=134003_126125_127760_100807_131676_131656_114744_125695_133678_120195_133967_132866_131602_133017_132911_133044_131246_132440_130762_132378_131517_118892_118867_118852_118831_118804_132841_132604_107315_133158_132782_130127_133352_133302_129653_127027_132538_133837_133473_131906_128891_133847_132552_133287_133387_131423_133215_133414_133916_110085_132354_133893_127969_123289_131755_131298_127416_131549_133728_128808_100459; Hm_lvt_287705c8d9e2073d13275b18dbd746dc=1561985898,1562900188,1562930631,1562931008; Hm_lvt_7d6994d7e4201dd18472dd1ef27e6217=1562814883,1562917177,1562919244,1562980079; SET_PB_IMAGE_WIDTH=391; BDUSS=lTN2RJMnliRXpYMkVZTWF0emRCQ3d4cjdybThEN1IzdGpxTEI5c1B2cFd5MUJkSVFBQUFBJCQAAAAAAAAAAAEAAAA3T50bMTY2OTEzODMwMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFY-KV1WPildMn; STOKEN=b9b4098b3f68faa05a0a493f5df1739e3fcec7d8d588524739c0f497534c9302; SEENKW=%E4%B8%89%E5%9B%BD%E6%9D%80%23%E6%9E%AA%E7%A5%9E%E7%BA%AA%23%E6%B1%82%E7%94%9F%E4%B9%8B%E8%B7%AF%23%E6%8A%80%E6%9C%AF%E5%AE%85%23%C8%FD%B9%FA%C9%B1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1563070081,1563073804,1563076073,1563153425; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1563154339'
        self.cookies = {i.split("=")[0]: i.split("=")[1] for i in self.cookies.split(";")}  # cookies 切割
        self.version = json.load(open('version_index.json', 'r', encoding='utf8'))
        self.phone_pd = pd.DataFrame(columns=['phone'])
        self.phone = json.load(open('match_phone_version.json', 'r', encoding='utf8'))

        exist_phone_pd = pd.read_csv(f'old_phone_configuration.csv', encoding='utf_8_sig')
        exist_phone_list = exist_phone_pd['phone'].tolist()
        tmp = []
        for v in self.phone.values():
            tmp.extend(v)
        print(f'还有{len(tmp) - len(exist_phone_list)}款手机数据没有收集')
        tmp_dict = {}
        for key, val in self.phone.items():
            tmp_dict[key] = []
            for v in val:
                if v not in exist_phone_list:
                    tmp_dict[key].append(v)
        self.phone = tmp_dict
        tmp = []
        for v in self.phone.values():
            tmp.extend(v)
        print(f'还有{len(tmp)}款手机数据没有收集')

        # 将信号与函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def start_requests(self):
        yield scrapy.Request(
            self.start_urls[0],
            callback=self.parse,
            cookies=self.cookies
        )

    # 爬虫结束时执行的函数
    def spider_closed(self, spider):
        print(f'收集了{self.phone_pd.shape[0]}款手机')

        old_data = pd.read_csv(f'old_phone_configuration.csv', encoding='utf_8_sig')

        tmp = old_data.copy()
        for index, row in self.phone_pd.iterrows():
            _idx = tmp.shape[0]
            for col in self.phone_pd.columns:
                tmp.at[_idx, col] = row[col]

        tmp.to_csv(f'old_phone_configuration.csv', encoding='utf_8_sig', index=False)
        self.phone_pd.to_csv(f'phone_configuration.csv', encoding='utf_8_sig', index=False)

    def parse(self, response):
        try:
            for key, phone_list in self.phone.items():
                for phone in phone_list:
                    url = 'http://detail.zol.com.cn' + self.version[phone]
                    yield scrapy.Request(
                        url,
                        callback=self.parse_phone_version,
                        cookies=self.cookies,
                        meta={'phone': phone}
                    )
        except BaseException as error:
            print(error)

    def parse_phone_version(self, response):
        phone = response.meta['phone']
        index = self.phone_pd.shape[0]
        # if response.xpath("//div[contains(@class,'info-list-box')]"):
        #     for div in response.xpath("//div[contains(@class,'info-list-box')]"):
        #         self.phone_pd.at[index, 'phone'] = phone
        #         configuration = div.xpath(".//label[@class='name']/text()").get()
        #         content = div.xpath(".//span[@class='product-link']/@title").get()
        #         if configuration not in self.phone_pd.columns:
        #             self.phone_pd[configuration] = None
        #         self.phone_pd.at[index, configuration] = content
        # else:
        #     for div in response.xpath("//div[contains(@class,'_j_param_inner')]"):
        #         self.phone_pd.at[index, 'phone'] = phone
        #         configuration = div.xpath(".//strong/text()").get()
        #         content = div.xpath(".//a/text()").get()
        #         if configuration not in self.phone_pd.columns:
        #             self.phone_pd[configuration] = None
        #         self.phone_pd.at[index, configuration] = content
        if _url := response.xpath("//a[contains(text(),'详细参数')]/@href").get():
            url = 'http://detail.zol.com.cn' + _url
        elif _url := response.xpath("//a[contains(text(),'查看完整参数')]/@href").get():
            url = 'http://detail.zol.com.cn' + _url
        else:
            print('没有找到数据入口')
            return

        # url = 'http://detail.zol.com.cn' + self.version[phone]
        yield scrapy.Request(
            url,
            callback=self.parse_phone_detail,
            cookies=self.cookies,
            meta={'phone': phone}
        )

    def parse_phone_detail(self, response):
        phone = response.meta['phone']
        index = self.phone_pd.shape[0]

        for tr in response.xpath("//div[@id='seriesParamTableBox']//tr"):
            self.phone_pd.at[index, 'phone'] = phone
            configuration = tr.xpath(".//th[contains(@data-num,'param')]/text()").get()
            if not (content := tr.xpath(".//td[1]//b/text()").get()) and not (content := tr.xpath(".//td[1]/text()").get()):
                continue
            if configuration not in self.phone_pd.columns:
                self.phone_pd[configuration] = None
            self.phone_pd.at[index, configuration] = content


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl('phone_configuration')
    process.start()
