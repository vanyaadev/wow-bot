
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By

from settings import Settings
from order import Order

import os
import time
import random

USER_DATA_DIR = os.getcwd()+'/ChromeProfile'
USER_DATA_DIR = r'C:\Users\ianti\AppData\Local\Google\Chrome\User Data'

def click(driver: Chrome, element):
    driver.execute_script("arguments[0].click()", element)

def wait_element(driver: Chrome, xpath: str):
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, xpath)
        )
    )

def random_sleep(a = 0.1, b = 0.2, delay = None):
    if delay:
        a += delay
        b += delay
    time.sleep(random.uniform(a, b))

class Bot:
    def __init__(self, settings: Settings = None):
        self.settings = settings

        opts = ChromeOptions()
        if USER_DATA_DIR:
            opts.add_argument('user-data-dir='+USER_DATA_DIR)
        self.driver = Chrome(executable_path=os.getcwd()+'/chromedriver.exe', options=opts)

    def authorize(self, login, password):
        self.driver.get('https://www.shasso.com/sso/login?action=login')
        self.driver.find_element_by_id('loginform-customers_email_address').send_keys(login)
        self.driver.find_element_by_id('loginform-customers_password').send_keys(password)

        time.sleep(0.5)
        click(self.driver, self.driver.find_element_by_xpath("//button[text()='Login']"))

    def add_order(self, order: Order, price: float):
        self.driver.get('https://www.g2g.com/sell/index')

        trade_selection = Select(self.driver.find_element_by_xpath('//select[@id="service"]'))
        trade_selection.select_by_value('1')

        wait_element(self.driver, '//select[@id="game"]')
        random_sleep(delay=0.3)

        game_selection = Select(self.driver.find_element_by_xpath('//select[@id="game"]'))
        game_selection.select_by_visible_text(
            f'World Of Warcraft ({order.region.upper()})'
        )

        wait_element(self.driver, "//h3[contains(text(), 'Product Details')]")
        random_sleep(delay=0.3)
        #------------------------------------------------------------------------------------------

        server_selection = Select(self.driver.find_element_by_xpath("//select[@id='server']"))
        server_selection.select_by_visible_text(order.server)
        random_sleep()

        faction_selection = Select(self.driver.find_element_by_xpath("//select[@id='faction']"))
        faction_selection.select_by_visible_text(order.faction)
        random_sleep()

        self.driver.find_element_by_id('C2cProductsListing_products_description').send_keys(order.description)

        currency_selection = Select(self.driver.find_element_by_xpath(
            "//select[contains(@id, 'products_base_currency')]"))
        currency_selection.select_by_value(order.currency.upper())
        random_sleep()

        self.driver.find_element_by_xpath("//input[@id='C2cProductsListing_products_price']") \
            .send_keys(str(price))
        random_sleep()

        self.driver.find_element_by_xpath("//input[@id='C2cProductsListing_forecast_quantity']") \
            .send_keys(str(order.stock))
        random_sleep()

        self.driver.find_element_by_xpath("//input[@id='C2cProductsListing_minimum_quantity']") \
            .send_keys(str(order.min_unit_per_order))
        random_sleep()

        delivery_widget = self.driver.find_element_by_class_name('create__action-delivery')
        for span in delivery_widget.find_elements_by_class_name('create__action-duration'):
            if span.text.lower() in order.delivery_option.lower():
                click(self.driver, span.find_element_by_tag_name('input'))
                random_sleep(delay=-0.05)

        online_hrs_selection = Select(self.driver.find_element_by_xpath(
            "//select[@id='C2cProductsListing_online_hr']"
        ))
        online_hrs_selection.select_by_value(str(order.online_hrs))
        random_sleep()

        offline_hrs_selection = Select(self.driver.find_element_by_xpath(
            "//select[@id='C2cProductsListing_offline_hr']"
        ))
        offline_hrs_selection.select_by_value(str(order.offline_hrs))
        random_sleep()

        click(self.driver, self.driver.find_element_by_xpath("//button[contains(text(), 'Submit')]"))

    def close(self):
        self.driver.close()


if __name__ == '__main__':
    bot = Bot()
    #bot.authorize('funnypig1606@gmail.com', 'zaqzaq')
    input()

    order = Order(
        region = 'eu',
        server = 'Classic - Golemagg',
        faction = 'Alliance',
        stock = 99999,
        currency = 'USD',
        description = 'test',
        min_unit_per_order = 99999,
        duration = 3,
        delivery_option = 'Face to face trade, Mail, Auction House',
        online_hrs = 2,
        offline_hrs = 7
    )
    bot.add_order(order, 1)
    input()

    bot.close()