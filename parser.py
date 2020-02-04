import requests
import logging
import time
import re

from bs4 import BeautifulSoup as bs
from threading import Thread
from dataclasses import dataclass

PARSE_FIRST_PAGES = 5
sellers_rating = dict()


def parse_list_of_servers(server_location: str):
    if server_location.lower() == 'eu':
        url = 'https://www.g2g.com/wow-eu/gold-2522-19248'
    else:
        url = 'https://www.g2g.com/wow-us/gold-2299-19249'

    page = requests.get(url).text
    soup = bs(page, 'html.parser')
    list_of_all_servers = soup.find('select', {'name': 'server', 'id': 'server'}).findChildren()[1:]

    servers_bfa = {}
    servers_classic = {}

    for server in list_of_all_servers:
        if 'Classic' in server.text:
            servers_classic[server.text] = server.get('value')
        else:
            servers_bfa[server.text] = server.get('value')

    return servers_classic, servers_bfa


eu_classic_servers, eu_bfa_servers = parse_list_of_servers("eu")
us_classic_servers, us_bfa_servers = parse_list_of_servers("us")


def make_url(region, server, faction):
    if region.lower() == 'us':
        url = 'https://www.g2g.com/wow-us/gold-2299-19249?sorting=price@asc&server='
        url += us_classic_servers[server] \
            if 'classic' in server.lower() \
            else us_bfa_servers[server]
    else:
        url = 'https://www.g2g.com/wow-eu/gold-2522-19248?sorting=price@asc&server='
        url += eu_classic_servers[server] \
            if 'classic' in server.lower() \
            else eu_bfa_servers[server]

    url += '&faction=542' if 'alliance' in faction.lower() else '&faction=543'
    url += '&page='

    return url


@dataclass
class GItem:
    min_quantity: int
    region: str
    fraction: str
    currency: str
    stock_amount: int
    server: str
    seller_name: str
    seller_rating: float
    delivery_time: int
    price: float
    url: str = ''

    def __str__(self):
        return ' '.join(self.__dict__.values())

    def __eq__(self, other):
        return self.url == other.url


class GoldParser(Thread):
    def __init__(self, url, proxy=None):
        super(GoldParser, self).__init__()

        self.url = url
        self.proxy = proxy
        self.result = []
        self.finished = False
        self.is_started = False
        self.product_amount = 0

        if proxy and type(proxy) == str:
            host_port, user, passw = proxy.split(',')
            self.proxy = {
                'http': f'http://{user}:{passw}@{host_port}',
                'https': f'http://{user}:{passw}@{host_port}'
            }

    def run(self):
        self.is_started = True

        try:
            self.result = self.get_items_list(1)
        except:
            self.result = []

        pages = min(self.product_amount // 10, PARSE_FIRST_PAGES)

        for page in range(2, pages + 1):
            try:
                for item in self.get_items_list(page):
                    if item not in self.result:
                        self.result.append(item)
            except:
                logging.error('Error at:\n' + self.url + str(page), exc_info=True)

        self.finished = True

    def get_items_list(self, page=1):
        url = self.url + str(page)
        region = 'US' if 'wow-us' in url else 'EU'
        html_page = requests.get(url, proxies=self.proxy).text
        html_page = html_page.replace('\n', ' ')
        html_page = ' '.join(html_page.split())

        soup = bs(html_page, 'lxml')

        if page == 1:
            text_amount = soup.find('span', class_='products__amount').text.split()[0]
            self.product_amount = int(text_amount)

        products = []

        for child in soup.find_all('li', class_='products__list-item js-accordion-parent'):
            if str(child).strip() == '':
                continue
            min_quantity = int(child.find('input', {'class': 'products__count-input'}).get('value').strip())
            seller_name = child.find('a', {'class': 'seller__name'}).get('href').strip()

            seller_url = 'https://www.g2g.com' + seller_name
            seller_name = seller_name.replace('/', '')

            if seller_url in sellers_rating.keys():
                seller_rating = float(sellers_rating[seller_url])
            else:
                page_of_seller = requests.get(seller_url, proxies=self.proxy).text
                soup2 = bs(page_of_seller, 'html.parser')
                seller_rating = soup2.find('span', {'class': 'user-statistic__percent'}).text[:-1]
                sellers_rating[seller_url] = seller_rating

            server_fraction = child.findAll('li', {'class': 'active'})
            if len(server_fraction) == 2:
                server = server_fraction[0].text.strip()
                fraction = server_fraction[1].text.strip()
            else:
                server = 'Undefined'
                fraction = server_fraction[0].text.strip()

            currency = child.find('span', {'class': 'products__exch-rate'}).text.strip()[-3:]
            stock = child.find('span', {'class': 'products__statistic-amount'}).text.strip().split()[0].split(',')
            stock = int(''.join(stock))

            delivery_time = int(child.find('span', class_='products__statistic-hours').text.split()[0].strip())

            url_of_item = child.find('a', {'class': 'products__name'}).get('href')

            price = float(child.find('span', {'class': 'products__exch-rate'}).text.strip().split()[-1][0:-3])

            item = GItem(
                min_quantity=min_quantity,
                region=region,
                fraction=fraction,
                currency=currency,
                stock_amount=stock,
                server=server,
                seller_rating=seller_rating,
                seller_name=seller_name,
                delivery_time=delivery_time,
                url=url_of_item,
                price=price
            )
            products.append(item)

        return products


def parse_items(region: str, server: str, faction: str, proxy: list = None):
    if proxy:  # BUILD PROXY DICTS
        for i in range(len(proxy)):
            host_port, user, passw = proxy[i].split(',')
            pr = {
                'http': f'http://{user}:{passw}@{host_port}',
                'https': f'http://{user}:{passw}@{host_port}'
            }
            proxy[i] = pr

    if server.lower() == 'classic':  # ALL CLASSIC SERVERS URLS
        servers = eu_classic_servers if region.lower() == 'eu' else us_classic_servers
        urls = [make_url(region, _server, faction, ) for _server in servers]
    elif server.lower() == 'bfa':  # ALL BFA SERVERS URLS
        servers = eu_classic_servers if region.lower() == 'eu' else us_classic_servers
        urls = [make_url(region, _server, faction) for _server in servers]
    else:
        urls = [make_url(region, server, faction)]  # SINGLE SERVER

    if not proxy:
        proxy = [None] * len(urls)
    proxy_size = len(proxy)

    threads = [GoldParser(urls[i], proxy[i % proxy_size]) for i in range(len(urls))]

    for t in threads:
        t.start()
        time.sleep(2)

    for t in threads:
        t.join()

    result = []
    for t in threads:
        result.extend(t.result)

    return result


if __name__ == '__main__':
    def test():
        # result = parse_items('us','classic',['217.69.6.173:33513,vBjSQM,14Jjxq'])
        # result = parse_items('us', 'classic')
        result = parse_items('us', 'Classic - Arugal')

        print(result)


    def proxy_test():
        url = 'https://api.myip.com'
        proxy = '217.69.6.173:33513'
        user = 'vBjSQM'
        passw = '14Jjxq'
        pr = {
            'https': f'http://{user}:{passw}@{proxy}'
        }
        print(pr)
        r = requests.get(url, proxies=pr)
        print(r.text)


    def profile_gold_parser():
        gp = GoldParser('https://www.g2g.com/wow-us/gold-2299-19249?server=30955&faction=543&sorting=price@asc&page=')
        gp.run()
        print(len(gp.result))
        print(gp.result)


    profile_gold_parser()
