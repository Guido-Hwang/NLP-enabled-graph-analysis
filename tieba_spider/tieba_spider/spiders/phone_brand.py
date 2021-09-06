# -*- coding: utf-8 -*-
import json
import re

import scrapy
# from scrapy.xlib.pydispatch import dispatcher
from pydispatch import dispatcher
from scrapy import signals


class PhoneBrandSpider(scrapy.Spider):
    '''
    利用api接口爬取个人信息
    '''
    name = 'phone_brand_spider'
    start_urls = ['http://mobile.zol.com.cn/manu_list.html']

    # 不同爬虫的设置
    # custom_settings = {
    #     "CONCURRENT_REQUESTS": 32
    # }

    def __init__(self):
        # 携带cookie登录
        self.cookies = 'BAIDUID=45FB8DA09A914E629390863C57F0DC4B:FG=1; BIDUPSID=45FB8DA09A914E629390863C57F0DC4B; PSTM=1559219844; TIEBAUID=c9d81907c343f58656236b9c; TIEBA_USERTYPE=771c50dd5a2a1babb2474f72; bdshare_firstime=1559460699558; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; IS_NEW_USER=c1fb106822622ad8692c2bf4; CLIENTWIDTH=400; CLIENTHEIGHT=922; H_WISE_SIDS=134003_126125_127760_100807_131676_131656_114744_125695_133678_120195_133967_132866_131602_133017_132911_133044_131246_132440_130762_132378_131517_118892_118867_118852_118831_118804_132841_132604_107315_133158_132782_130127_133352_133302_129653_127027_132538_133837_133473_131906_128891_133847_132552_133287_133387_131423_133215_133414_133916_110085_132354_133893_127969_123289_131755_131298_127416_131549_133728_128808_100459; Hm_lvt_287705c8d9e2073d13275b18dbd746dc=1561985898,1562900188,1562930631,1562931008; Hm_lvt_7d6994d7e4201dd18472dd1ef27e6217=1562814883,1562917177,1562919244,1562980079; SET_PB_IMAGE_WIDTH=391; BDUSS=lTN2RJMnliRXpYMkVZTWF0emRCQ3d4cjdybThEN1IzdGpxTEI5c1B2cFd5MUJkSVFBQUFBJCQAAAAAAAAAAAEAAAA3T50bMTY2OTEzODMwMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFY-KV1WPildMn; STOKEN=b9b4098b3f68faa05a0a493f5df1739e3fcec7d8d588524739c0f497534c9302; SEENKW=%E4%B8%89%E5%9B%BD%E6%9D%80%23%E6%9E%AA%E7%A5%9E%E7%BA%AA%23%E6%B1%82%E7%94%9F%E4%B9%8B%E8%B7%AF%23%E6%8A%80%E6%9C%AF%E5%AE%85%23%C8%FD%B9%FA%C9%B1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1563070081,1563073804,1563076073,1563153425; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1563154339'
        self.cookies = {i.split("=")[0]: i.split("=")[1] for i in self.cookies.split(";")}  # cookies 切割
        self.phone_brand_dict = {}

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
        with open('phone_version.json', 'w', encoding='utf8')as fp:
            json.dump(self.phone_brand_dict, fp, ensure_ascii=False)

    def parse(self, response):
        try:
            for li in response.xpath("//ul[@class='BrandsList clearfix']//li"):
                brand = li.xpath(".//img/@alt").get()
                # self.phone_brand_dict[brand]=[]
                if re.search('（', brand):
                    brand = re.findall('(.*?)（(.*?)）', brand)
                    self.phone_brand_dict[brand[0][1]] = brand[0]
                else:
                    brand_list=[]
                    brand_list.append(brand)
                    self.phone_brand_dict[brand] = brand_list

                print(brand)
        except BaseException as error:
            print(error)


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl('phone_brand_spider')
    process.start()
