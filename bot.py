import os
import time

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import Select

from settings import Settings
from order import Order
from utils import click, random_sleep, wait_element, enable_download_headless

# USER_DATA_DIR = os.getcwd()+'/ChromeProfile'
USER_DATA_DIR = r'C:\Users\ianti\AppData\Local\Google\Chrome\User Data'
DEFAULT_DOWNLOAD_DIRECTORY = os.path.join(os.getcwd(), 'Downloads')


class Bot:
    def __init__(self, settings: Settings = None):
        self.settings = settings

        opts = ChromeOptions()
        if USER_DATA_DIR:
            opts.add_argument('user-data-dir=' + USER_DATA_DIR)
        opts.add_experimental_option("prefs", {
            "download.default_directory": DEFAULT_DOWNLOAD_DIRECTORY,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })

        self.driver = Chrome(executable_path=os.getcwd() + '/chromedriver.exe', options=opts)

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
        # ------------------------------------------------------------------------------------------

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

    def active_orders(self, region='eu'):
        # create set of files that are currently in the directory
        current_xls_files = {file for file in os.listdir(DEFAULT_DOWNLOAD_DIRECTORY)
                             if file.endswith('.xls')}

        if region == 'eu':
            url = 'https://www.g2g.com/sell/manage?service=1&game=2522&type=1'
        else:
            url = 'https://www.g2g.com/sell/manage?service=1&game=2299&type=1'
        self.driver.get(url)

        enable_download_headless(self.driver, DEFAULT_DOWNLOAD_DIRECTORY)
        click(self.driver, self.driver.find_element_by_partial_link_text('Download List'))
        time.sleep(3)

        new_file_name = {file for file in os.listdir(DEFAULT_DOWNLOAD_DIRECTORY)
                         if file.endswith('.xls') and file not in current_xls_files}.pop()
        new_file_path = os.path.join(DEFAULT_DOWNLOAD_DIRECTORY, new_file_name)


        os.remove(new_file_path)


    def close(self):
        self.driver.close()


if __name__ == '__main__':
    bot = Bot()
    # bot.authorize('funnypig1606@gmail.com', 'zaqzaq')
    input()


    def test_add_order():
        order = Order(
            region='eu',
            server='Classic - Golemagg',
            faction='Alliance',
            stock=99999,
            currency='USD',
            description='test',
            min_unit_per_order=99999,
            duration=3,
            delivery_option='Face to face trade, Mail, Auction House',
            online_hrs=2,
            offline_hrs=7
        )

        order_2 = Order(
            region='eu',
            server='Classic - Golemagg',
            faction='Horde',
            stock=8888,
            currency='USD',
            description='test 2',
            min_unit_per_order=8888,
            duration=3,
            delivery_option='Face to face trade, Mail, Auction House',
            online_hrs=4,
            offline_hrs=10
        )

        bot.add_order(order_2, price=1.5)

    bot.active_orders()
    input()

    bot.close()
