# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
import json
import time
from scrapy import signals
# from scrapy.xlib.pydispatch import dispatcher
from pydispatch import dispatcher
import requests
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
    ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from scrapy.http import HtmlResponse
from twisted.web.client import ResponseFailed
from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import tieba_spider


class TiebaSpiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn???t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# url = 'http://1669138300.v4.dailiyun.com/query.txt?key=NP5418F974&word=&count=&rand=false&detail=false'
url = 'http://linshenhe.v4.dailiyun.com/query.txt?key=NP424225C7&word=&count=1&rand=false&ltime=0&norepeat=false&detail=false'


class TiebaSpiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    ALL_EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError, TunnelError)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # request.meta['proxy'] = 'http://116.218.46.47:57114'
        ### ??????????????????5S?????????????????????IP
        tieba_spider.end_time = time.time()
        proxyport = 57114  # ??????IP??????
        proxyusernm = "linshenhe"  # ????????????
        proxypasswd = "dgut7486"  # ????????????

        if (datetime.datetime.fromtimestamp(tieba_spider.end_time) - datetime.datetime.fromtimestamp(
                tieba_spider.start_time)).seconds >= 10:
            # tieba_spider.start_time = time.time()
            while True:
                req = requests.get(url)
                proxy = req.text
                proxy = proxy.replace('\n', '').replace('\r', '')  # ???????????????
                if proxy:
                    # tieba_spider.proxy_ip = "http://" + proxy
                    tieba_spider.proxy_ip = "http://" + proxyusernm + ":" + proxypasswd + "@" + proxy
                    # proxyurl = "http://" + proxyusernm + ":" + proxypasswd + "@" + proxy + ":" + "%d" % proxyport
                    # request.meta['proxy'] = "http://" + proxy
                    request.meta['proxy'] = tieba_spider.proxy_ip
                    print('??????ip', tieba_spider.proxy_ip)
                    break
                else:
                    print('ip ??????')
                    time.sleep(5)
        else:
            request.meta['proxy'] = tieba_spider.proxy_ip
            print('??????ip',tieba_spider.proxy_ip)

        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        # ???????????????????????????
        if isinstance(exception, self.ALL_EXCEPTIONS):
            # ??????????????????????????????
            print('Got exception: %s' % (exception))
            # ??????????????????response????????????spider
            response = HtmlResponse(url='exception')
            return response
        # ??????????????????????????????
        print('not contained exception: %s' % exception)

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProcessAllExceptionMiddleware(object):
    ALL_EXCEPTIONS = (defer.TimeoutError, TimeoutError, DNSLookupError,
                      ConnectionRefusedError, ConnectionDone, ConnectError,
                      ConnectionLost, TCPTimedOutError, ResponseFailed,
                      IOError, TunnelError)

    def process_response(self, request, response, spider):
        # ??????????????????40x/50x???response
        if str(response.status).startswith('4') or str(response.status).startswith('5'):
            # ???????????????????????????response???spider???????????????url==''?????????response
            # response = HtmlResponse(url='')
            # return response
            print(response.status)
            return request
        # ????????????????????????
        return response

    def process_exception(self, request, exception, spider):
        # ???????????????????????????
        if isinstance(exception, self.ALL_EXCEPTIONS):
            # ??????????????????????????????
            print('Got exception: %s' % (exception))
            # ??????????????????response????????????spider
            response = HtmlResponse(url='exception')
            return response
        # ??????????????????????????????
        print('not contained exception: %s' % exception)


class MyRetryMiddleware(RetryMiddleware):

    def process_exception(self, request, exception, spider):
        ## ???????????????????????????reponse,????????????IP,?????????request??????????????????????????????
        if '10061' in str(exception) or '10060' in str(exception):
            while True:
                url = 'http://1669138300.v4.dailiyun.com/query.txt?key=NP5418F974&word=&count=&rand=false&detail=false'
                req = requests.get(url)
                proxy = req.text
                proxy = proxy.replace('\n', '').replace('\r', '')  # ???????????????
                if proxy:
                    request.meta['proxy'] = "http://" + proxy
                    break
                else:
                    print('ip ??????')
                    time.sleep(5)

        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)
