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


class YstVideoCrawlerPipeline:
    client = None
    db = None
    collection = None
    download_threads = 64
    def open_spider(self,spider):
        self.client = pymongo.MongoClient("mongodb://mediaSource:mediaSource123@10.0.1.148:27017/qiubai")
        self.db = self.client["qiubai"]

    def process_item(self, item, spider):
        # download video
        print("process_item item=", item)
        if item == None  :
            return item
        # print("process_item: item[video_name]=", item['video_name'])

        m3u8path = item['m3u8path']
        mp4path = item['mp4path']
        video_name = item['video_name']
        m3u8_downloader = os.path.join(os.path.abspath(os.path.curdir),
                                    r"yst_video_crawler\spiders\N_m3u8DL-CLI")
        print("m3u8_downloader=", m3u8_downloader)
        command = u"N_m3u8DL-CLI  \"{}\" --workDir \"{}\" --saveName \"{}\" --maxThreads {} --minThreads {} --enableDelAfterDone --disableDateInfo --stopSpeed 1024 --noProxy"
        command_exec = command.format(m3u8path, mp4path, video_name,
                                          self.download_threads, self.download_threads)
        command_exec = command_exec.encode("gbk")
        print("command_exec=", command_exec)
        os.system(str(command_exec, encoding="gbk"))
        data = dict(item)
        self.db["video"].insert(data)
        return item
    def close_spider(self,spider):
        self.client.close()



