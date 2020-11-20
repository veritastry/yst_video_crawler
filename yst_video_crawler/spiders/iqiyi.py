import json
import os
import re

import requests
import scrapy
from scrapy import crawler
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from yst_video_crawler.items import IqiyiVideoCrawlerItem
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from redis import  Redis
# from scrapy.utils.project import get_project_settings
from selenium.webdriver.chrome.options import Options

class IqiyiSpider(CrawlSpider):
    name = 'iqiyi'
    allowed_domains = ['www.iqiyi.com']

    start_urls = [
        r'https://child.iqiyi.com/?vfrm=pcw_home&vfrmblk=C&vfrmrst=712211_channel_ertong'
    ]
    link_series = LinkExtractor(allow=r'a_[A-Za-z0-9]+.html')
    # playpage_link = LinkExtractor(allow=r'v_[A-Za-z0-9]+.html')
    rules = (
        Rule(link_series, callback='parse_series', follow=True),
        # Rule(playpage_link, callback='parse_play_page', follow=True),
    )
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_driver_path = r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\chromedriver.exe"
    redis_conn = None
    # chrome_path = self.s
    # chrome_driver_path
    def __init__(self, *args, **kwargs):
        super(IqiyiSpider, self).__init__(*args, **kwargs)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = self.chrome_path
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches',
                                       ['enable-automation'])
        self.browser = webdriver.Chrome(
            executable_path=self.chrome_driver_path,
            chrome_options=chrome_options,
            options=option)
        self.redis_conn = Redis(host='127.0.0.1', port=6379)

    def parse_series(self, response):
        print("parse_series response.url=", response.url)
        li_list = response.xpath('//*[@id="widget-tab-3"]/div[5]/div/ul/li')
        # print('li_list=',li_list)
        for li in li_list:
            episode = li.xpath('./div[1]/a/@href').extract_first()
            # 将剧集的url存入redis的set中

            print('episode=', episode)
            episode_url = 'https:' + episode
            yield scrapy.Request(url=episode_url, callback=self.parse_play_page)
            # ex = self.redis_conn.sadd('episode_urls', episode_url)
            # if ex == 1:
            #     print('该url没有被爬取过，可以进行数据的爬取')
            #     yield scrapy.Request(url=episode_url, callback=self.parse_play_page)
            # else:
            #     print('数据还没有更新，暂无新数据可爬取！')

    def parse_play_page(self, response):
        print("parse_detail")
        item = IqiyiVideoCrawlerItem()
        title = response.xpath('//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/em/text()').extract_first()
        serials_name = response.xpath('//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/a/@title').extract_first()
        if title == '':
            return None
        url_download = os.path.join(os.path.abspath(os.path.curdir),
                                    u"{}.m3u8".format(title))
        item['video_name'] = title
        item['m3u8path'] = url_download
        item['mp4path'] = os.path.join(r'D:\dev\python\crawler\yst_video_crawler' )
        item['serials_name'] = serials_name
        item['video_url'] = response.url
        # item['mp4path'] =  get_project_settings().get('video_store_path')
        # scrapy.logging.debug("  url_download=", url_download)
        print("  url_download=", url_download)
        script_iqiyi = open(r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\iqiyi.js").read()
        self.browser.execute_script(script_iqiyi)
        dash_url = self.browser.execute_script("return window.dashUrl;")
        # print(dash_url)
        cookies = self.browser.get_cookies()
        cookie = ""
        for ckitem in cookies:
            cookie += "{}={}; ".format(ckitem["name"], ckitem["value"])
        headers = {}
        headers["Host"] = "cache.video.iqiyi.com"
        headers["Connection"] = "keep-alive"
        headers[
            "User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
        headers["Accept"] = "*/*"
        headers["Sec-Fetch-Site"] = "same-site"
        headers["Sec-Fetch-Mode"] = "no-cors"
        headers["Referer"] = "https://www.iqiyi.com/v_19rurcgqzs.html"
        headers["Accept-Encoding"] = "gzip, deflate, br"
        headers["Accept-Language"] = "zh-CN,zh;q=0.9"
        headers["Cookie"] = cookie
        response = requests.get(dash_url, headers=headers, timeout=15)
        result = response.text
        data = re.findall("{\".*\"}", result, re.DOTALL)
        data = json.loads(data[0])
        videos = data["data"]["program"]["video"]
        # item["vlist"] = videos
        # scrapy.logging.info("videos",videos)
        # print("videos",videos)
        for video in videos:
            if video["_selected"]:
                m3u8 = video["m3u8"]
                with open(url_download, "w") as fd:
                    fd.write(m3u8)
                break
        yield item
    def closed(self, spider):
        print("IqiyiSpider close ")
        self.browser.quit()