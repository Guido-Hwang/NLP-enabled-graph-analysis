# -*- coding: utf-8 -*-
import json
import re
from urllib import parse
from urllib.parse import unquote

import pandas as pd
import scrapy
from pydispatch import dispatcher
from scrapy import signals

import tieba_spider


class BarClassiferSpider(scrapy.Spider):
    '''
    将用户关注的贴吧进行分类
    '''
    name = 'bar_classifer_spider'
    start_urls = ['https://tieba.baidu.com/p/6296537898']
    # 不同爬虫pipeline设置
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            # 'tieba_spider.middlewares.TiebaSpiderDownloaderMiddleware': 542,
            # 'tieba_spider.middlewares.ProcessAllExceptionMiddleware': 543,
            # 'tieba_spider.middlewares.ProxyMiddleware': 544,
        }
    }

    def __init__(self):
        # 携带cookie登录
        self.cookies = 'BAIDUID=45FB8DA09A914E629390863C57F0DC4B:FG=1; BIDUPSID=45FB8DA09A914E629390863C57F0DC4B; PSTM=1559219844; TIEBAUID=c9d81907c343f58656236b9c; TIEBA_USERTYPE=771c50dd5a2a1babb2474f72; bdshare_firstime=1559460699558; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; IS_NEW_USER=c1fb106822622ad8692c2bf4; CLIENTWIDTH=400; CLIENTHEIGHT=922; H_WISE_SIDS=134003_126125_127760_100807_131676_131656_114744_125695_133678_120195_133967_132866_131602_133017_132911_133044_131246_132440_130762_132378_131517_118892_118867_118852_118831_118804_132841_132604_107315_133158_132782_130127_133352_133302_129653_127027_132538_133837_133473_131906_128891_133847_132552_133287_133387_131423_133215_133414_133916_110085_132354_133893_127969_123289_131755_131298_127416_131549_133728_128808_100459; Hm_lvt_287705c8d9e2073d13275b18dbd746dc=1561985898,1562900188,1562930631,1562931008; Hm_lvt_7d6994d7e4201dd18472dd1ef27e6217=1562814883,1562917177,1562919244,1562980079; SET_PB_IMAGE_WIDTH=391; BDUSS=lTN2RJMnliRXpYMkVZTWF0emRCQ3d4cjdybThEN1IzdGpxTEI5c1B2cFd5MUJkSVFBQUFBJCQAAAAAAAAAAAEAAAA3T50bMTY2OTEzODMwMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFY-KV1WPildMn; STOKEN=b9b4098b3f68faa05a0a493f5df1739e3fcec7d8d588524739c0f497534c9302; SEENKW=%E4%B8%89%E5%9B%BD%E6%9D%80%23%E6%9E%AA%E7%A5%9E%E7%BA%AA%23%E6%B1%82%E7%94%9F%E4%B9%8B%E8%B7%AF%23%E6%8A%80%E6%9C%AF%E5%AE%85%23%C8%FD%B9%FA%C9%B1; Hm_lvt_98b9d8c2fd6608d564bf2ac2ae642948=1563070081,1563073804,1563076073,1563153425; Hm_lpvt_98b9d8c2fd6608d564bf2ac2ae642948=1563154339'
        self.cookies = {i.split("=")[0]: i.split("=")[1] for i in self.cookies.split(";")}  # cookies 切割

        self.floor = 1
        tieba_spider.csv_file_name = f'user_L{self.floor}_bar'
        try:
            self.user_pd = pd.read_csv(f'{tieba_spider.data_path}{tieba_spider.csv_file_name}_classify.csv',
                                       encoding='utf_8_sig')
            print('进行查漏补缺')
            print(self.user_pd.shape[0])
            print(f"还有{self.user_pd[self.user_pd['forum_category'].isnull()].shape[0]}个贴吧，因为某种原因未能归类")
        except BaseException as error:
            print(error)
            self.user_pd = pd.read_csv(f'{tieba_spider.data_path}{tieba_spider.csv_file_name}.csv',
                                       encoding='utf_8_sig',
                                       engine='python')
            self.user_pd['forum_category'] = None
            # self.user_pd['forum_category'] = self.user_pd['forum_category'].astype('object')  ###  这一句有什么用,会影响第二次归类
        else:
            print(f"有{self.user_pd[self.user_pd['bar_name'].isnull()].shape[0]}没有贴吧名字的行,开始过滤掉这些行")
            self.user_pd.dropna(subset=['bar_name'], inplace=True)

        # self.user_pd['forum_category'].replace('nan', '', inplace=True)
        # self.user_pd['forum_category'] = self.user_pd['forum_category'].astype('str')
        # 将信号与函数绑定
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        # 读取json文件内容,返回字典格式
        with open('bar_type.json', 'r', encoding='utf8') as fp:
            tieba_spider.bar_type = json.load(fp)

        ### 贴吧目录
        self.forum_class = json.load(open('bar_catalog.json', 'r', encoding='utf8'))
        # 将目录中的二维列表转化为一维
        self.forum_class_list = []
        for data in self.forum_class.values():
            self.forum_class_list.extend(data)

        self.cnt = 0

    # 爬虫结束时执行的函数
    def spider_closed(self, spider):
        print(f"还有{self.user_pd[self.user_pd['forum_category'].isnull()].shape[0]}个贴吧，因为某种原因未能归类")
        print(self.user_pd.shape[0])
        print(self.user_pd[self.user_pd['forum_category'].isnull()].shape[0])
        self.user_pd.to_csv(f"{tieba_spider.data_path}{tieba_spider.csv_file_name}_classify.csv",
                            encoding='utf_8_sig', index=False)
        with open('bar_type.json', 'w', encoding='utf8') as fp:
            json.dump(tieba_spider.bar_type, fp, ensure_ascii=False)

    def parse(self, response):
        for index, rows in self.user_pd[self.user_pd['forum_category'].isnull()].iterrows():  ### 再次爬取，上次爬取有丢失
            # for index, rows in self.user_pd.iterrows():
            try:
                forum = rows['bar_name']
                if forum not in tieba_spider.bar_type.keys():  # 如果之前没有查询过
                    # if forum in tieba_spider.bar_type.keys():  # 如果之前没有查询过
                    # forum = forum.replace('吧', '')
                    ### 访问贴吧目录
                    yield scrapy.Request(
                        url=f"https://tieba.baidu.com/f?kw={unquote(forum.replace('吧', ''), 'utf-8')}",
                        callback=self.parse_bar_category,
                        meta={'index': index, 'forum': forum},
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.16 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
                        },
                        cookies=self.cookies,
                        # dont_filter=True,
                    )
                else:
                    self.user_pd.at[index, 'forum_category'] = tieba_spider.bar_type[forum]  # 字典没有问题
                if not index % 1000:
                    print(f'已经完成{index / self.user_pd.shape[0]}')

            except BaseException as error:
                print(error)

    def parse_bar_category(self, response):
        """
        通过用户查询api查询用户关注贴吧的类型以及等级
        """
        self.cnt += 1
        if not self.cnt % 100:
            print(f'第{self.cnt}次查询贴吧目录')
            # 保存贴吧分类
            with open('bar_type.json', 'w', encoding='utf8') as fp:
                json.dump(tieba_spider.bar_type, fp, ensure_ascii=False)
        try:
            index = response.meta['index']
            forum = response.meta['forum']

            result = re.search('fd=(.*?)&ie=utf-8&sd=(.*?)">', response.text, flags=re.DOTALL)  # 爬取一级目录分类名字
            if result:
                if result.group(2) == '手机':
                    bar_category = '手机'
                else:
                    bar_category = result.group(1)
            else:
                if re.search('抱歉，根据相关法律法规和政策，相关结果不予展现', response.text, flags=re.DOTALL):
                    bar_category = '违规封禁'
                elif re.search('百度安全验证', response.text, flags=re.DOTALL):
                    print('遇到安全验证了,重新请求')
                    # url = 'http://http.tiqu.qingjuhe.cn/getip?num=1&type=1&pack=55294&port=1&lb=1&pb=4&regions='
                    # req = requests.get(url)
                    # proxy = req.text
                    # tieba_spider.proxy_ip = "http://" + proxy
                    # print('切换IP', proxy)
                    # time.sleep(5)
                    # proxy = proxy.replace('\n', '').replace('\r', '')  # 去除换行符

                    ### 重新访问贴吧目录
                    # yield scrapy.Request(
                    #     url=f"https://tieba.baidu.com/f?kw={unquote(forum, 'utf-8')}",
                    #     callback=self.parse_bar_category,
                    #     meta={'index': index, 'forum': forum},
                    #     headers={
                    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.16 Safari/537.36",
                    #         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
                    #     },
                    #     cookies=self.cookies,
                    #     dont_filter=True,
                    #     priority=10  # Request请求中priority(优先级)默认值是0,越大优先级越大,允许是负值
                    # )
                    return
                    # self.crawler.engine.close_spider(self, "被反爬了，请开启IP代理池")
                elif not result:  # 为空
                    bar_category = '无'
                else:
                    print(result)

            ### 对字符创中的URL编码进行解码
            bar_category = parse.unquote(bar_category)
            ### 直接提取以及目录
            if bar_category in self.forum_class.keys():  # 如果是一级目录
                tieba_spider.bar_type[forum] = bar_category
            # elif bar_category in self.forum_class_list:  # 检测是否在贴吧二级目录
            #     data = [data for data in self.forum_class.values() if bar_category in data]
            #     bar_category = list(self.forum_class.keys())[
            #         list(self.forum_class.values()).index(data[0])]  # 查找相应的以及目录
            #     tieba_spider.bar_type[forum] = bar_category
            else:
                print('百度贴吧没有收录这个分类')  # 无,违规封禁 这个2类别除外
                self.forum_class[bar_category] = []  # 新建一大类
                tieba_spider.bar_type[forum] = bar_category
                result = re.search('fd=(.*?)ie=utf.*?sd=(.*?)"', response.text, flags=re.DOTALL)  # 爬取一级目录分类名字
                if result.group(2):  # 次目录 添加
                    self.forum_class[bar_category].append(result.group(2))

                with open('bar_catalog.json', 'w', encoding='utf8') as fp:
                    json.dump(self.forum_class, fp, ensure_ascii=False)
                with open('bar_type.json', 'w', encoding='utf8') as fp:
                    json.dump(tieba_spider.bar_type, fp, ensure_ascii=False)

            self.user_pd.at[index, 'forum_category'] = bar_category

        except BaseException as e:
            print(e)

    def complete_bar_category(self, response):
        try:
            index = response.meta['index']
            forum = response.meta['forum']
            result = re.search('>百度贴吧 &gt; (.*?)<', response.text, flags=re.DOTALL)  # 爬取一级目录分类名字
            if result:
                bar_category = result.group(1)
                if bar_category in self.forum_class:
                    self.forum_class[bar_category].append(forum)
                else:  # 创建新的一类
                    self.forum_class[bar_category] = []
                    self.forum_class[bar_category].append(forum)
                    tieba_spider.bar_type[forum] = bar_category
            else:
                print('出错检查')
            # 重新将目录中的二维列表转化为一维，来添加新的类别
            self.forum_class_list = []
            for data in self.forum_class.values():
                self.forum_class_list.extend(data)

            self.user_pd.at[index, 'forum_category'] = bar_category

            with open('bar_catalog.json', 'w', encoding='utf8') as fp:
                json.dump(self.forum_class, fp, ensure_ascii=False)
            with open('bar_type.json', 'w', encoding='utf8') as fp:
                json.dump(tieba_spider.bar_type, fp, ensure_ascii=False)
        except BaseException as e:
            print(e)


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    process.crawl('bar_classifer_spider')
    process.start()
