import datetime
import json
import os
import re
import threading
from time import sleep

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
    count = 0
    # chrome_path = self.s
    # chrome_driver_path
    def __init__(self, *args, **kwargs):
        super(IqiyiSpider, self).__init__(*args, **kwargs)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = self.chrome_path
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        option = ChromeOptions()
        option.add_experimental_option('excludeSwitches',
                                       ['enable-automation'])
        self.lock = threading.Lock()
        self.browser = webdriver.Chrome(
            executable_path=self.chrome_driver_path,
            chrome_options=chrome_options,
            options=option)
        self.redis_conn = Redis(host='127.0.0.1', port=6379)
        # load link from Redis


    def parse_series(self, response):
        url = response.url
        if re.search(r'https:\/\/www.iqiyi.com\/a_[A-Za-z0-9]+.html', url) != None:
            #  get url for redis
            episode_links = self.redis_conn.hget('album', response.url)
            print('episode from redis=', episode_links)
            # epsd_str = str(episode_links, encoding='UTF-8')
            if episode_links != None:
                elist = str(episode_links, encoding='UTF-8').split(',')
                for eps in elist:
                    print("epsd=", eps)
                    if eps != None and eps != '':
                        yield scrapy.Request(eps, callback=self.parse_play_page)
                print("parse_series episode_links=", episode_links)
        return
        if re.search(r'https:\/\/www.iqiyi.com\/a_[A-Za-z0-9]+.html', response.url) != None:
            browser = self.browser
            self.retry_times = 0
            while True:
                self.retry_times += 1
                content = ''
                browser.get(response.url)
                page_text = browser.page_source
                getiqiyiEpisodeLinkjs = open(
                    r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\iqiyiEpisode.js").read()
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
                content = ''.join(episode_links)
                self.lock.release()
                if (len(episode_links) > (alist_length - 1) * 50) or self.retry_times >= 3:
                    print("data is  ok or times complete, stop retry crawl")
                    break
            print('serials url=', response.url, 'episode total= ', len(episode_links))
            for link in episode_links:
                yield scrapy.Request(url=link, callback=self.parse_play_page)












        # get all episode link
        # print('response=', response)
        # self.lock.acquire()
        # getiqiyiEpisodeLinkjs = open(r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\iqiyiEpisode.js").read()
        # self.browser.execute_script(getiqiyiEpisodeLinkjs)
        # episode_links = self.browser.execute_script("return window.episodeLink;")
        # print('serials url=', response.url, 'episode total= ', len(episode_links))
        # for elink in episode_links:
        #     print('episodeLink=', elink)
        #     yield scrapy.Request(url=elink, callback=self.parse_play_page)
        # self.lock.release()

        # album_tab = self.browser.find_elements_by_xpath('//*[@id="widget-tab-3"]/div[2]/ul/li')
        # for album_li in album_tab:
        #     album_li.click()
        #     sleep(1)
        #     li_list = self.browser.find_elements_by_xpath('//*[@id="widget-tab-3"]/div[5]/div/ul/li')
        #     print('#################li_list len= {}##########'.format(len(li_list)))
        #     i = 1
        #     for vli in li_list:
        #         episode_url = vli.find_element_by_xpath('./div[1]/a').get_attribute('href')
        #         print('i=', i, 'episode_url=', episode_url, 'title=', vli.find_element_by_xpath('./div[1]/a').get_attribute('title'))
        #         # episode_url = 'https:' + episode
        # scrapy.Request(url=episode_url, callback=self.parse_play_page)
        # i += 1
        # ex = self.redis_conn.sadd('episode_url', episode_url)
        # if ex == 1:
        #     print('该url没有被爬取过，可以进行数据的爬取')
        #     scrapy.Request(url=episode_url, callback=self.parse_play_page)
        # else:
        #     print('数据还没有更新，暂无新数据可爬取！')

    def parse_play_page(self, response):
        print("parse_detail")
        item = IqiyiVideoCrawlerItem()
        title = response.xpath('//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/em/text()').extract_first()
        serials_name = response.xpath('//*[@id="block-C"]/div[1]/div/div/div/div/div[1]/h1/a/@title').extract_first()
        if title == '':
            return None
        item['serials_name'] = serials_name
        item['video_name'] = title
        # mkdir m3u8_store_path
        # os.mkdir(os.path.join(os.path.abspath(os.path.curdir), serials_name))
        m3u8_store_path = os.path.join(os.path.abspath(os.path.curdir), serials_name,
                                    u"{}.m3u8".format(title))
        item['m3u8path'] = m3u8_store_path
        item['mp4path'] = os.path.join(r'D:\dev\python\crawler\yst_video_crawler', serials_name)

        item['video_url'] = response.url
        # item['mp4path'] =  get_project_settings().get('video_store_path')
        # scrapy.logging.debug("  m3u8_store_path=", m3u8_store_path)
        print("  m3u8_store_path=", m3u8_store_path)
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
                with open(m3u8_store_path, "w") as fd:
                    fd.write(m3u8)
                break
        yield item
    def closed(self, spider):
        print("IqiyiSpider close")
        self.browser.quit()