from urllib.parse import urlencode
import pymongo
from lxml.etree import XMLSyntaxError
from requests.exceptions import ConnectionError
import requests
from pyquery import PyQuery as pq
from config import *

client = pymongo.MongoClient(MONGODB_URL)
db = client[MONGO_DB]

base_url = 'http://weixin.sogou.com/weixin?'

headers = {
    'Cookie': 'CXID=99DB0153E348C231A44DBC8C4B5B6BF0; ad=qyllllllll2BhhRSlllllVXaw29llllltswz6yllll9lllllpCxlw@@@@@@@@@@@; SUID=911AF2725C68860A59CB20D1000C772E; IPLOC=CN1100; SUV=1507264293883345; ABTEST=8|1507264296|v1; SNUID=1138D05021247BF872D7F06122B7F04B; weixinIndexVisited=1; sct=2; JSESSIONID=aaa1sHZzcqIIVaM6qqz6v; ppinf=5|1507264706|1508474306|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo2MzolRTglOEIlOTQlRTglOEIlOTQlRTQlQkIlQTUlRTglOEIlOTQlRTQlQkIlQTUlRTglOEIlOTQlRTglOEIlOTR8Y3J0OjEwOjE1MDcyNjQ3MDZ8cmVmbmljazo2MzolRTglOEIlOTQlRTglOEIlOTQlRTQlQkIlQTUlRTglOEIlOTQlRTQlQkIlQTUlRTglOEIlOTQlRTglOEIlOTR8dXNlcmlkOjQ0Om85dDJsdUxBSERUZjVLMi1SUTJPTnl3S0dMajBAd2VpeGluLnNvaHUuY29tfA; pprdig=PLqT9E7zVi0hQ5rGZWKPb33CDM3TjhPp0rbCy0TkEc1i990NIWKWfqKpFXhWOXOc9SkoEvMsnu1ocnZ65SKIexGJPAq8knhzYNmZPP1W9uKo5ts9UQPd0A4IC8s8PGtO9iqI3z8VxHahLHvfTZ_kv4DtjW9VYAdz8tYIvo8bV7k; sgid=18-31293203-AVnXCMKZEFSMCrz5u5NbRI0; ppmdig=15072647060000004ba34ae5a47b534ac6b6650753859268',
    'Host': 'weixin.sogou.com',
    # 'Pragma': 'no-cache',
    # 'Referer': 'http://weixin.sogou.com/weixin?query=%E9%A3%8E%E6%99%AF&type=2&page=22&ie=utf8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}

proxy = None
max_count = 5


def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html1(url, count=1):
    print('Crawling', url)
    print('Trying Count', count)
    global proxy
    if count == max_count:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, headers=headers, allow_redirects=False, proxies=proxies)
        else:
            response = requests.get(url, headers=headers, allow_redirects=False)  # requests默认跳转，用False取消跳转。
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            # Need proxy
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy', proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)


def get_html(url, count=1):
    print('Crawling', url)
    print('Trying Count', count)
    global proxy
    if count >= MAX_COUNT:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxies = {
                'http': 'http://' + proxy
            }
            response = requests.get(url, allow_redirects=False, headers=headers, proxies=proxies)  # requests默认跳转，用False取消跳转。
            # print(response.url)
        else:
            response = requests.get(url, allow_redirects=False, headers=headers)
        if response.status_code == 200:
            return response.text
        if response.status_code == 302:
            # Need Proxy
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy', proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None
    except ConnectionError as e:
        print('Error Occurred', e.args)
        proxy = get_proxy()
        count += 1
        return get_html(url, count)


def get_index(keyword, page):
    data = {
        'query': keyword,
        'type': 2,
        'page': page
    }

    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html


def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')


def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def pares_detail(html):

    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content').text()
        date = doc('#post-date').text()
        nickname = doc('#js_profile_qrcode > div > strong').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title': title,
            'content': content,
            'date': date,
            'nickname': nickname,
            'wechat': wechat
        }
    except XMLSyntaxError:
        return None


def save_to_mongo(data):
    if db['artcles'].update({'title': data['title']}, {'$set': data}, True):
        print('Saved to Mongo', data['title'])
    else:
        print('Saved to Mongo Failed', data['title'])


def main():
    for page in range(1, 101):
        html = get_index(KEYWORD, page)
        # print(html)
        if html:
            article_urls = parse_index(html)
            for article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = pares_detail(article_html)
                    print(article_data)
                    save_to_mongo(article_data)

if __name__ == '__main__':
    main()
