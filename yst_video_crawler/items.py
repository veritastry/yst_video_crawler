# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YstVideoCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass
class IqiyiVideoCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    video_name = scrapy.Field()
    # vid = scrapy.Field()
    mp4path = scrapy.Field()
    m3u8path = scrapy.Field()
    video_url = scrapy.Field()
    serials_name = scrapy.Field()
    pass