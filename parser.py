from bs4 import BeautifulSoup as bs
import requests
from threading import Thread
from dataclasses import dataclass
import logging
import time

sellers_rating = {

}

def parse_list_of_servers(server_location: str):
    url = ''
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
            servers_classic[server.get('value')]=server.text

        else:
            servers_bfa[server.get('value')]=server.text

    return servers_classic, servers_bfa



eu_classic_servers,eu_bfa_servers = parse_list_of_servers("eu")
us_classic_servers,us_bfa_servers = parse_list_of_servers("us")


@dataclass
class GItem:
    min_quantity: int
    region: str
    fraction: str
    currency: str
    stock_amount: int
    server: str
    seller_rating: float
    price: float
    url: str = ''


    def __str__(self):
        return ' '.join(self.__dict__.values())


class GoldParser(Thread):
    def __init__(self, url, proxy):
        super(GoldParser, self).__init__()

        self.url = url
        self.proxy = proxy
        self.result = []
        self.finished = False
        self.is_started = False

    def run(self):
        # TODO: define number of pages. probably on the first page. and then parse from second in the loop
        self.is_started = True
        pages = 1
        for page in range(pages):
            try:
                self.result.extend(self.get_items_list(page))
            except:
                logging.error('Error at:\n' + self.url + str(page), exc_info=True)

        self.finished = True

    def get_items_list(self, page=1):
        # TODO: rewrite using enums. another ONCE parsing will be required
        url = self.url + str(page)
        region = 'US' if 'wow-us' in url else 'EU'
        page = requests.get(url).text
        soup = bs(page, 'html.parser')

        products = []

        for child in soup.findAll('li',{'class':'products__list-item js-accordion-parent'}):
            min_quantity = int(child.find('input',{'class':'products__count-input'}).get('value').strip())
            seller_name = child.find('a',{'class':'seller__name'}).get('href')

            seller_url = 'https://www.g2g.com' + seller_name.strip()

            seller_rating = 0.0
            if(seller_url in sellers_rating.keys()):
                seller_rating=float(sellers_rating[seller_url])
            else:
                page_of_seller = requests.get(seller_url).text
                soup2 = bs(page_of_seller, 'html.parser')
                seller_rating = soup2.find('span', {'class': 'user-statistic__percent'}).text[:-1]
                sellers_rating[seller_url]=seller_rating

            page_of_seller = requests.get(seller_url).text

            server_fraction = child.findAll('li', {'class': 'active'})
            if len(server_fraction)==2:
                server = server_fraction[0].text.strip()
                fraction = server_fraction[1].text.strip()
            else:
                server = 'Undefined'
                fraction = server_fraction[0].text.strip()

            currency = child.find('span', {'class': 'products__exch-rate'}).text.strip()[-3:]
            stock = child.find('span', {'class': 'products__statistic-amount'}).text.strip().split()[0].split(',')
            stock = ''.join(stock)

            url_of_item = child.find('a', {'class': 'products__name'}).get('href')
            products_number = child.findAll('a', {'href': url_of_item})[1].text[1:-1]

            price = float(child.find('span', {'class': 'products__exch-rate'}).text.strip().split()[-1][0:-3])

            item = GItem(
                min_quantity=min_quantity,
                region=region,
                fraction=fraction,
                currency=currency,
                stock_amount=stock,
                server=server,
                seller_rating=seller_rating,
                url = url_of_item + seller_url,
                price = price
            )
            products.append(item)

        return products


def parse_items(region: str, server: str, proxy: list, server_name=None):
    # server: classic / bfa
    urls = []
    if region.lower() == 'us':
        url = 'https://www.g2g.com/wow-us/gold-2299-19249?&server='
        urls = [
            url + _server+ '&page='
            for _server in (us_classic_servers.keys()
                            if server.lower() == 'classic'
                            else us_bfa_servers.keys())
        ]
    else:
        url = 'https://www.g2g.com/wow-eu/gold-2522-19248?&server='

        urls = [url + _server + '&page=' for _server in (eu_classic_servers.keys() if server.lower() == 'classic' else eu_bfa_servers.keys())]

    if not proxy:
        proxy = [None] * len(urls)
    proxy_size = len(proxy)

    threads = [GoldParser(urls[i], proxy[i % proxy_size]) for i in range(len(urls))]

    active_threads = 0
    finished_threads = 0
    max_workers = 6

    while finished_threads != len(threads):
        while active_threads >= max_workers:
            time.sleep(0.5)

        for t in threads:
            if not t.is_started:
                t.start()
                break

        finished_threads = sum([1 for t in threads if t.finished])

    for t in threads:
        t.join()

    result = []
    for t in threads:
        result.extend(t.result)

    return result

  
if __name__ == '__main__':
    result = parse_items('us','classic',[])
    print(result)

