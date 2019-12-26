import os
import re
import urllib.request
import js2py
import requests
from lxml import etree
from clint.textui import progress
import fire
from loguru import logger
import time
from progressbar import *

from multiprocessing.dummy import Pool as ThreadPool


headers = {
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
}
proxies = {}

def run(offset):
    global keyworld
    if not os.path.exists(keyworld):
        os.mkdir(keyworld)
    keywd = urllib.request.quote(keyworld)
    url='https://www.pornhub.com/video/search?search=%s&page=%d'%(keywd,offset)
    list_page(url)

def list_page(url):
    res = requests.get(url)
    if res.status_code==200:
        main_page = res.text
        video = {}
        pattern = re.compile('<span.*?class=\"title\">.*?<a.*?href=\"(.*?)\".*?title=\"(.*?)\".*?class=.*?</a>.*?</span>',re.S)
        items = re.findall(pattern,main_page)

        pool = ThreadPool(4) #双核电脑
        video_list = []
        for item in items[6:-1]:
            url = 'https://www.pornhub.com'+item[0]
            video_list.append(url)
        pool.map(detail_page, video_list)#多线程工作
        pool.close()
        pool.join()
    else:
        print("请求网页失败，请检查网页URL是否正确------------")
def download(url, name, filetype):
    global keyworld
    filepath = '%s/%s.%s' % (keyworld, name, filetype)
    print("正在下载: "+filepath)
    if os.path.exists(filepath):
        print('已存在:%s '%(name))
        print('')
        return
    else:
        response = requests.get(url, headers=headers, proxies=proxies, stream=True)
        with open(filepath, "wb") as file:
            total_length = int(response.headers.get('content-length'))
            for ch in progress.bar(response.iter_content(chunk_size=2391975),
                                   expected_size=(total_length / 2391975) + 1):
                if ch:
                    file.write(ch)
            # do something
            print("成功下载："+filepath)
            print("=================================================================")
            print("")


def exeJs(js):
    flashvars = re.findall('flashvars_\d+', js)[0]
    res = js2py.eval_js(js + flashvars)
    if res.quality_720p:
        return res.quality_720p
    elif res.quality_480p:
        return res.quality_480p
    elif res.quality_240p:
        return res.quality_240p
    else:
        logger.error('parse url error')

def detail_page(url):
    s = requests.Session()
    resp = s.get(url, headers=headers, proxies=proxies)
    html = etree.HTML(resp.content)

    title = ''.join(html.xpath('//h1//text()')).strip()

    js_temp = html.xpath('//script/text()')
    for j in js_temp:
        if 'flashvars' in j:
            js = ''.join(j.split('\n')[:-8])
            videoUrl = exeJs(js)
            download(videoUrl, title, 'mp4')
            continue

keyworld = input("请输入搜索关键字:")
pages = input("请输入要爬取的页数:")
if __name__ == '__main__':
    pool = ThreadPool(8) #双核电脑
    tot_page = []
    for i in range(1,int(pages)+1): #提取1到10页的内容
        tot_page.append(i)
    pool.map(run, tot_page)#多线程工作
    pool.close()
    pool.join()