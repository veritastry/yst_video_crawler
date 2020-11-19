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
# from scrapy.utils.project import get_project_settings
from selenium.webdriver.chrome.options import Options

class IqiyiSpider(CrawlSpider):
    name = 'iqiyi'
    allowed_domains = ['www.iqiyi.com']

    start_urls = [
        r'https://child.iqiyi.com/?vfrm=pcw_home&vfrmblk=C&vfrmrst=712211_channel_ertong'
    ]
    # link_series = LinkExtractor(allow=r'a_[A-Za-z0-9]+.html')
    playpage_link = LinkExtractor(allow=r'v_[A-Za-z0-9]+.html')
    rules = (
        # Rule(link_series, callback='parse_series', follow=True),
        Rule(playpage_link, callback='parse_play_page', follow=True),
    )
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    chrome_driver_path = r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\chromedriver.exe"

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

    def parse_series(self, response):
        print("parse_item")
        item = IqiyiVideoCrawlerItem()
        item['video_name'] = response.xpath(
            '//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/a/@title/text()').extract()
        +response.xpath(
            '//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/em/text()'
        ).extract()
        # print("video=", video_name)
        # item['vid'] =
        # item['mp4path'] =
        # item['m3u8path'] =
        # item['dldate'] =

    def parse_play_page(self, response):
        print("parse_detail")
        item = IqiyiVideoCrawlerItem()
        title = response.xpath('//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/em/text()').extract_first()
        if title == '':
            return None
        url_download = os.path.join(os.path.abspath(os.path.curdir),
                                    u"{}.m3u8".format(title))
        item['video_name'] = title
        item['m3u8path'] = url_download
        item['mp4path'] = os.path.join(r'D:\dev\python\crawler\yst_video_crawler' )
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