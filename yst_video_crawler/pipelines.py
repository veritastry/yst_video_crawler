# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# useful for handling different item types with a single interface
import os

import pymongo
from itemadapter import ItemAdapter
# from scrapy.pipelines.images import ImagesPipeline
import scrapy
from  redis import  Redis
from scrapy.pipelines.files import FilesPipeline
from yst_video_crawler.items import IqiyiVideoCrawlerItem
from scrapy.settings import Settings
import logging

logger = logging.getLogger(__name__)

class YstVideoDatabasePipeline(object):
    client = None
    db = None
    collection = None
    download_threads = 64
    redis_conn = None

    def open_spider(self, spider):
        self.client = pymongo.MongoClient("mongodb://mediaSource:mediaSource123@10.0.1.148:27017/qiubai")
        self.db = self.client["qiubai"]
        self.redis_conn = spider.redis_conn

    def process_item(self, item, spider):
        # download video
        print("YstVideoDatabasePipeline process_item item=", item)
        if item is None:
            return item
        # logger.info("process_item: item[video_name]=", item['video_name'])
        data = dict(item)
        self.db["video"].insert(data)
        self.redis_conn.lpush('episode_detail', data)
        return item

    def close_spider(self, spider):
        self.client.close()


class YstVideoDownloadPipeline(FilesPipeline):
    download_threads = 64
    def get_media_requests(self, item, info):
        print("YstVideoDownloadPipeline  ")
        video_name = IqiyiVideoCrawlerItem(item).get("video_name", "")
        serials_name = IqiyiVideoCrawlerItem(item).get("serials_name", "")
        m3u8path = IqiyiVideoCrawlerItem(item).get("m3u8path", "")
        mp4path = IqiyiVideoCrawlerItem(item).get("mp4path", "")
        print("YstVideoDownloadPipeline   m3u8path=", m3u8path)
        if len(m3u8path) > 0:
            print("len(m3u8path>0")
            # settings = Settings()
            # m3u8path = item['m3u8path']
            # logger.info("settings.get FILES_STORE=", settings.get('FILES_STORE'))
            # mp4path = os.path.join(r'D:\dev\python\crawler\yst_video_crawler', serials_name)
            # logger.info("mp4path=", mp4path)
            m3u8_downloader = os.path.join(os.path.abspath(os.path.curdir),
                                        r"yst_video_crawler\spiders\N_m3u8DL-CLI")
            logger.info("m3u8_downloader=", m3u8_downloader)
            command = u"N_m3u8DL-CLI  \"{}\" --workDir \"{}\" --saveName \"{}\" --maxThreads {} --minThreads {} --enableDelAfterDone --disableDateInfo --stopSpeed 1024 --noProxy"
            command_exec = command.format(m3u8path, mp4path, video_name,
                                          self.download_threads, self.download_threads)
            command_exec = command_exec.encode("utf-8")
            print("command_exec=", command_exec)
            yield os.system(str(command_exec, encoding="utf-8"))
        else:
            print("len(m3u8path<=0")

    def item_completed(self, results, item, info):
        print("YstVideoDownloadPipeline item_completed")
        return  item
    def file_path(self, request, response=None, info=None):
        return  "."
        logger.info("file_path")
