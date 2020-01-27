from selenium.webdriver import Chrome
from time import sleep
from bs4 import BeautifulSoup
import requests

page = requests.get('https://www.g2g.com/wow-eu/gold-2522-19248?&page=1').text
soup = BeautifulSoup(page,'html.parser')
button = soup.find("a",{'id':'lazy-load-btn'})

products_amount =  int(soup.find('span',{'class':'products__amount'}).text.split()[0])

products = []
current_page = '1'

while len(products)<products_amount:
    url = 'https://www.g2g.com/wow-eu/gold-2522-19248?&page='+current_page
    print("url="+url)
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    for child in soup.findAll('li',{'class':'products__list-item js-accordion-parent'}):
        #to do later
        print("add_to_products")

    current_page = str(int(current_page)+1)
