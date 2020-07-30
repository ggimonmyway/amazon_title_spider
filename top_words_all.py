import os
from UserAgent import UserAgent1
from analyze_word import Analyze
from multiprocessing import Process,Queue
import time
import datetime
import requests
from lxml import etree
# import sys
# from functools import partial
# from PyQt5.QtWidgets import QApplication, QMainWindow

# import title_gui

ua = UserAgent1()
proxypool_url = 'http://192.168.11.209:5555/random'
# print(ua.user_agent())

def get_random_proxy():
    """
    get random proxy from proxypool
    :return: proxy
    """
    return requests.get(proxypool_url).text.strip()

class title_Spider(object):
    def __init__(self, keyword):
        '''headers::浏览器头
           path :: 文件路径
           keyword::关键词
        '''
        self.headers = {'user-agent': ua.user_agent(),
                        'cookie': ua.cookies(),
                        'accept-ch': 'ect, rtt, downlink',
                        'accept - ch - lifetime': '86400',
                        'cache - control': 'no - cache',
                        'content - encoding': 'gzip',
                        'content - language': 'en-US',
                        'content - type': 'text/html',
                        'charset':'UTF-8',
                        'server':'Server'}

        self.path = self.mk_path()
        self.keyword = keyword
        self.baseurl = 'https://www.amazon.com/s?k={kw}'.format(kw=self.keyword)
        self.analyze = Analyze()
        self.good_kinds = {}


    @classmethod
    def mk_path(self):
        path = os.getcwd()
        work_file = str(datetime.date.today())
        dir_st = os.listdir(path)
        work_path = os.path.join(path, work_file)
        if work_file not in dir_st:
            os.makedirs(work_path)
        return work_path


    def get_html(self, url):
        '''获取html代码'''
        proxy = get_random_proxy()
        print('get random proxy', proxy)
        proxies = {'http': 'http://' + proxy}
        try:
            text = requests.get(url, headers=self.headers, proxies=proxies, timeout=5).text
            if 'Robot Check' in text:
                print('出现验证码,请更换ip')
                return self.get_html(url)
            else:
                return text
        except:
            print('连接出现错误，准备重试')
            time.sleep(1)
            return self.get_html(url)

    def get_page_title(self, url):
        '''
        :param text: html文本
        :return: 首页titles
        '''
        text = self.get_html(url)
        html = etree.HTML(text)
        a_ls = html.xpath('//a[@class="a-link-normal a-text-normal"]')
        good_kind = 'page_title'
        for a in a_ls:
            title = a.xpath('span/text()')[0]
            href = 'https://www.amazon.com/' + a.xpath('@href')[0]
            yield (good_kind, title, href)


    def get_bstitle(self, url):
        text = self.get_html(url)
        html = etree.HTML(text)
        # 8.商品种类
        kinds_of_commodity = html.xpath('//div[@id="zg-right-col"]/h1/span/text()')[0]

        list_lis = html.xpath('//*[@id="zg-ordered-list"]//li')
        if list_lis:
            print('list_lis 长度', len(list_lis))
            bs_info = []
            for each_li in list_lis:
                # 商品名称
                title = each_li.xpath('./span/div/span/a/span/div/img/@alt')[0]
                # 详情页链接
                link_normal ='https://www.amazon.com/' + each_li.xpath('./span/div/span/a[@class="a-link-normal"]/@href')[0]
                bs_info.append((kinds_of_commodity, title, link_normal))
            return bs_info
        else:
            print("没有数据，程序结束")

    def get_bshref(self, url):
        '''
        获取bestseller页面的链接
        :return: list
        '''
        text = self.get_html(url)
        html = etree.HTML(text)
        bs_hrefs = html.xpath('//span/a[contains(@href, "bestseller")]/@href')
        bs_kind =html.xpath('//span/a[contains(@href, "bestseller")]/text()')
        return bs_hrefs, bs_kind

    def write_html(self, html):
        with open('D:/test2.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def to_text(self, title, keyword1):
        '''
        :param title: title
        :return:
        '''
        title = title.replace('\n', '').strip(' ')
        path = self.path + '/' + self.keyword + '_' + keyword1 + '.txt'
        print('>>>>已抓取：{title}....<<<<<'.format(title = title[:30]))
        with open(path, 'a', encoding='utf-8') as f:
            f.write(title + '\n')

    def bestseller(self, q):
        while q.empty() is not True:
            url = q.get()
            print('正在抓取详情页', url)
            bshref, good_kind = self.get_bshref(url)
            if bshref != []:
                bs_kind = good_kind[-1]
                bsurl = 'https://www.amazon.com/' + bshref[-1]
                if bs_kind in self.good_kinds:
                    print('此商品bestseller类目已被抓取:', bs_kind)
                    self.good_kinds[bs_kind] += 1
                else:
                    bs_info = self.get_bstitle(bsurl)
                    self.good_kinds[bs_kind] = 1
                    for info in bs_info:
                        # print('>>>>已抓取：{title}....<<<<<'.format(title=info[1][:10]))
                        self.to_text(info[1], info[0])
            else:
                print('此详情页无bestseller链接：', url)

q = Queue()

def run(keyword):
    base_url = 'https://www.amazon.com/s?k={k}&page={p}'
    spider = title_Spider(keyword)
    path = spider.path
    for page in range(1, 2):
        url = base_url.format(k=keyword, p=page)
        print('正在抓取', url)  # 抓取首页
        # spider.write_html(text)
        page_info = spider.get_page_title(url)
        for info in page_info:
            # print(info)
            # print('>>>>已抓取：{title}....<<<<<'.format(title=info[1][:10]))
            spider.to_text(info[1], info[0])
            if page  == 1:
                url = info[2]
                q.put(url)
    print('\n---------------首页数据已抓取完毕------------\n开始bestseller页数据抓取')
    print('queue 开始大小 %d' % q.qsize())
    p_lst = []
    for i in range(6):
        p = Process(target=spider.bestseller, args=(q,))  # 注意args里面要把q对象传给我们要执行的方法，这样子进程才能和主进程用Queue来通信
        p.start()
        p_lst.append(p)
    for p in p_lst:
        p.join()
    print(spider.good_kinds)
    print('文件存储位置', path)


if __name__ == '__main__':
    keyword = input('请输入关键词:')
    run(keyword)
    print('程序运行结束')

