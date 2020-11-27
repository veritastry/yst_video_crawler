# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
import json
import logging
import os
import re
import threading
import time
from time import sleep
import redis

import requests
from scrapy import signals
from scrapy import responsetypes
from scrapy.http import HtmlResponse, TextResponse
# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from goto import with_goto

class YstVideoCrawlerSpiderMiddleware:
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

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class YstVideoCrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    def __init__(self, *args, **kwargs):
        self.lock = threading.Lock()
        self.count = 0
        self.retry_times = 0
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    @with_goto
    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        print("process_request ")
        if re.search(r'https:\/\/www.iqiyi.com\/a_[A-Za-z0-9]+.html', request.url) != None:
            browser = spider.browser
            redis_conn = spider.redis_conn
            self.retry_times = 0
            self.count += 1
            if self.count > 2:
                return
            while True:
                self.retry_times += 1
                content = ''
                browser.get(request.url)
                page_text = browser.page_source
                getiqiyiEpisodeLinkjs = open(r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\iqiyiEpisode.js").read()
                self.lock.acquire()
                browser.execute_script(getiqiyiEpisodeLinkjs)
                alist_length = browser.execute_script("return window.alist_length;")
                print('alist_length = ', alist_length)
                start_time = datetime.datetime.now()
                sleep(30 + alist_length * 5)
                stop_time = datetime.datetime.now()
                cost = stop_time - start_time
                print("sleep   wait cost %s second" % (cost.seconds))
                episode_links = browser.execute_script("return window.episodeLink;")
                for epsd in episode_links:
                    content = content + epsd + ','
                self.lock.release()
                if (len(episode_links) > (alist_length-1)*50) or self.retry_times >= 3:
                    print("data is  ok or times complete, stop retry crawl")
                    break
            print('serials url=', request.url, 'episode total= ', len(episode_links))
            ex = redis_conn.hset('album', request.url, content)
            print("stored to redis")
            if ex != None:
                print('该url没有被爬取过，可以进行数据的爬取')
            else:
                print('数据还没有更新，暂无新数据可爬取！')
            new_response = HtmlResponse(url=request.url,
                                        body=page_text,
                                        encoding='utf-8',
                                        request=request)
            return new_response
        else:
            browser = spider.browser
            browser.get(request.url)
            page_text = browser.page_source
            new_response = HtmlResponse(url=request.url,
                                        body=page_text,
                                        encoding='utf-8',
                                        request=request)
            return new_response
        # if re.search(r'https:\/\/www.iqiyi.com\/v_[A-Za-z0-9]+.html', request.url) != None:
        #     browser = spider.browser
        #     browser.get(request.url)
        #     page_text = browser.page_source
        #     new_response = HtmlResponse(url=request.url,
        #                                 body=page_text,
        #                                 encoding='utf-8',
        #                                 request=request)
        #     return new_response
        # return None

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
        spider.logger.info('process_exception: %s' % spider.name)
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
