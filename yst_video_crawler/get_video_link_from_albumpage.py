from time import sleep

from lxml import etree
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_driver_path = r"D:\dev\python\crawler\yst_video_crawler\yst_video_crawler\spiders\chromedriver.exe"

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_path
option = ChromeOptions()
option.add_experimental_option('excludeSwitches',
                               ['enable-automation'])

browser = webdriver.Chrome(
    executable_path=chrome_driver_path,
    chrome_options=chrome_options,
    options=option)

browser.get('https://www.iqiyi.com/a_19rrhcw3h9.html')


page_source = browser.page_source
album_tab = browser.find_elements_by_xpath('//*[@id="widget-tab-3"]/div[2]/ul/li')
i = 0
for album_li in album_tab:
    album_li.click()
    sleep(1) # 非常重要， 否则没有更新页面数据
    li_list = browser.find_elements_by_xpath('//*[@id="widget-tab-3"]/div[5]/div/ul/li')
    print('#################li_list ####################')

    for vli in li_list:
        i += 1
        episode = vli.find_element_by_xpath('./div[1]/a').get_attribute('href')
        print('i=', i, 'episode=', episode, 'title=', vli.get_attribute('data-order'))
        # episode_url = 'https:' + episode
browser.quit()






