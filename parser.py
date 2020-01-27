from selenium.webdriver import Chrome
from time import sleep
from bs4 import BeautifulSoup
import requests

class GItem:
    def __init__(self, min_quantity, region, fraction, currency, stock, server, seller_rating):
        self.min_quantity = min_quantity
        self.region= region
        self.fraction=fraction
        self.currency=currency
        self.stock=stock
        self.server=server
        self.seller_rating=seller_rating

    def __str__(self):
        return self.min_quantity + ' ' + self.region +' ' + self.fraction +' ' + self.currency \
               +' ' + self.stock +' ' + self.server +' ' + self.seller_rating


def get_items_list():
    url = 'https://www.g2g.com/wow-eu/gold-2522-19248?&page=1'
    region = url[24:26]
    page = requests.get(url).text
    soup = BeautifulSoup(page,'html.parser')
    button = soup.find("a",{'id':'lazy-load-btn'})

    products_amount =  int(soup.find('span',{'class':'products__amount'}).text.split()[0])
    print(products_amount)
    products = []
    current_page = 1

    while len(products)<products_amount:
        url = 'https://www.g2g.com/wow-eu/gold-2522-19248?&page='+str(current_page)

        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html.parser')

        for child in soup.findAll('li',{'class':'products__list-item js-accordion-parent'}):
            min_quantity = child.find('input',{'class':'products__count-input'}).get('value').strip()
            seller_name = child.find('a',{'class':'seller__name'}).get('href')
            page_of_seller =requests.get('https://www.g2g.com'+seller_name).text
            soup2=BeautifulSoup(page_of_seller, 'html.parser')

            seller_rating = soup2.find('span',{'class':'user-statistic__percent'}).text

            server_fraction = child.findAll('li', {'class': 'active'})
            if len(server_fraction)==2:
                server = server_fraction[0].text.strip()
                fraction = server_fraction[1].text.strip()
            else:
                server = 'Undefined'
                fraction = server_fraction[0].text.strip()

            currency = child.find('span', {'class': 'products__exch-rate'}).text.strip()[-3:]
            stock = child.find('span', {'class': 'products__statistic-amount'}).text.strip().split()[0]


            item = GItem(min_quantity,region,fraction,currency,stock,server,'0')
            products.append(item)

        current_page = current_page+1
    return products

get_items_list()