import os
import time
import xlrd
import logging
import datetime as dt
import sys

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import Select

from settings import Settings
from order import Order
from utils import click, random_sleep, wait_element, enable_download_headless, orders_from_excel
from telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, filename='LOG.txt', filemode='a')

# USER_DATA_DIR = os.getcwd()+'/ChromeProfile'
USER_DATA_DIR = r'C:\Users\ianti\AppData\Local\Google\Chrome\User Data'
DEFAULT_DOWNLOAD_DIRECTORY = os.path.join(os.getcwd(), 'Downloads')

if not os.path.exists(DEFAULT_DOWNLOAD_DIRECTORY):
    os.mkdir(DEFAULT_DOWNLOAD_DIRECTORY)


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

        self.chat_messages = dict()
        self.telegram_bot = TelegramBot()

    def authorize(self, login, password):
        self.driver.get('https://www.shasso.com/sso/login?action=login')
        self.driver.find_element_by_id('loginform-customers_email_address').send_keys(login)
        self.driver.find_element_by_id('loginform-customers_password').send_keys(password)

        time.sleep(0.5)
        click(self.driver, self.driver.find_element_by_xpath("//button[text()='Login']"))

    def add_order(self, order: Order, price: float):
        logging.info(f'[{dt.datetime.now().isoformat()}] Add order: [{order}] with price {price}')

        self.driver.get('https://www.g2g.com/sell/index')

        try:
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

        except Exception as e:
            logging.info(f'[{dt.datetime.now().isoformat()}] Error adding order: ' + str(e))

    def change_order(self, order: Order):
        logging.info(f'[{dt.datetime.now().isoformat()}] Changing order #{order.listing_number}')

        if order.region.lower() == 'eu':
            self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2522&type=0')
        else:
            self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2299')

        try:
            tr = self.driver.find_element_by_id(f'c2c_{order.listing_number}')
        except:
            logging.info(f'[{dt.datetime.now().isoformat()}] Order #{order.listing_number} not changed! Reason: not found')
            return

        def change_field(text):
            wait_element(self.driver, '//span[@class="editable-clear-x"]', timeout=2)
            click(self.driver, self.driver.find_element_by_class_name('editable-clear-x'))
            random_sleep()
            self.driver.find_element_by_class_name('input-large').send_keys(str(text))
            click(self.driver, self.driver.find_element_by_xpath("//button[@class='btn btn--green editable-submit']"))
            random_sleep(delay=0.5)

        try:
            class_name = ['g2g_actual_quantity', 'g2g_minimum_quantity', 'g2g_products_price']
            value = [str(order.stock), str(order.min_unit_per_order), str(order.price)]

            for i in range(len(class_name)):
                wait_element(self.driver, f'//a[contains(@class, "{class_name[i]}")]', timeout=2)
                field_to_write = tr.find_element_by_class_name(class_name[i])
                if field_to_write.text.strip() != value[i]:
                    click(self.driver, field_to_write)
                    random_sleep(delay=0.1)
                    change_field(value[i])

                    field_name = class_name[i][4:]
                    logging.info(
                        f'[{dt.datetime.now().isoformat()}] ' +
                        f'Order #{order.listing_number} Field "{field_name}" changed to {value[i]}')

            # CHANGE ONLINE / OFFLINE HOURS

            selection_classes = ['g2g_online_hr', 'g2g_offline_hr']
            selection_values = [str(order.online_hrs), str(order.offline_hrs)]

            for i in range(len(selection_classes)):
                wait_element(self.driver, f'//a[contains(@class, "{class_name[i]}")]', timeout=2)
                field_to_write = tr.find_element_by_class_name(selection_classes[i])
                if field_to_write.text.strip() != selection_values[i]:
                    click(self.driver, field_to_write)
                    random_sleep(delay=0.1)

                    selection = Select(self.driver.find_element_by_class_name('input-large'))
                    selection.select_by_visible_text(selection_values[i])
                    click(self.driver, self.driver.find_element_by_xpath("//button[@class='btn btn--green editable-submit']"))
                    random_sleep(delay=0.5)

                    field_name = selection_classes[i][4:]
                    logging.info(
                        f'[{dt.datetime.now().isoformat()}] ' +
                        f'Order #{order.listing_number} Field "{field_name}" changed to {selection_values[i]}')

        except:
            logging.info(f'[{dt.datetime.now().isoformat()}] Order #{order.listing_number} not changed! Error: ' +
                         str(sys.exc_info()[0]))
            return

        time.sleep(1)
        logging.info(f'[{dt.datetime.now().isoformat()}] Order #{order.listing_number} successfully changed')

    def active_orders(self, region='eu'):
        logging.info(f'[{dt.datetime.now().isoformat()}] Started parsing active orders. Region: {region}')

        orders = []
        try:
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

            orders = orders_from_excel(new_file_path, just_active=True)

            os.remove(new_file_path)
        except Exception as e:
            logging.info(f'[{dt.datetime.now().isoformat()}] Error parsing active orders: ' + str(e))

        logging.info(f'[{dt.datetime.now().isoformat()}] Parsed active orders successfully. Return {len(orders)} orders')
        return orders

    def activate_all(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Activate all orders started')

        def activate():
            try:
                click(self.driver, self.driver.find_element_by_id('check-all'))
            except:  # No inactive orders
                return

            for span in self.driver.find_elements_by_class_name('manage__action-text'):
                if 'relist' in span.text.lower():
                    click(self.driver, span)
                    break

            time.sleep(1)
            click(self.driver, self.driver.find_element_by_xpath("//button[@class='btn btn--green product-action-page']"))

        self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2522&type=2')
        activate()

        self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2299&type=2')
        activate()

        logging.info(f'[{dt.datetime.now().isoformat()}] Orders activated')

    def deactivate_all(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Deactivate all orders started')

        def deactivate():
            try:
                click(self.driver, self.driver.find_element_by_id('check-all'))
            except: # No inactive orders
                return

            for span in self.driver.find_elements_by_class_name('manage__action-text'):
                if 'deactivate' in span.text.lower():
                    click(self.driver, span)
                    break

            time.sleep(1)
            click(self.driver, self.driver.find_element_by_xpath("//button[@class='btn btn--green product-action-page']"))

        self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2522&type=1')
        deactivate()

        self.driver.get('https://www.g2g.com/sell/manage?service=1&game=2299&type=1')
        deactivate()

        logging.info(f'[{dt.datetime.now().isoformat()}] Orders deactivated')

    def parse_messages(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Parse messages started')

        self.driver.get('https://chat.g2g.com/')
        time.sleep(1)
        wait_element(self.driver, "//input[@placeholder='Search']", timeout=30)

        usernames = list(map(lambda _div: _div.text.strip(),
                             self.driver.find_elements_by_class_name('e0e0377cd4a6e9dcec5b509beb659b00')))

        # FIRST PARSING
        if self.chat_messages == dict():
            usernames = iter(usernames)
            for div in self.driver.find_elements_by_class_name('_4f2b5b47720b4ebd54a6176cbe380a22'):
                self.chat_messages[next(usernames)] = [div.text.strip()]

            return

        try:
            for chat_number in range(3):
                try:
                    username = usernames[chat_number]
                    if username not in self.chat_messages:
                        self.chat_messages[username] = ['']

                    click(self.driver,
                          self.driver.find_elements_by_class_name('ff2c5f905d92eebf09f923b4a8bd3870')[chat_number])

                    try:
                        wait_element(self.driver, "//div[@message-id]", timeout=20)
                    except TimeoutError:  # No messages
                        continue
                    time.sleep(2)

                    new_messages = list(map(lambda span: span.text.strip(),
                                            self.driver.find_elements_by_xpath("//div[@message-id]")))

                    if new_messages[-1].split('\n')[0] == self.chat_messages[username][-1].split('\n')[0]:
                        continue

                    new_messages_start_index = len(new_messages) - 1

                    while new_messages_start_index > 0:
                        if new_messages[new_messages_start_index].split('\n')[0] == \
                                self.chat_messages[username][-1].splt('\n')[0]:
                            break
                        new_messages_start_index -= 1
                    new_messages = new_messages[new_messages_start_index:]

                    msg_to_send = username + '\n' + '\n\n'.join([
                        '\n'.join(nm.split('\n')[::-1]) for nm in new_messages
                    ])

                    self.chat_messages[username].extend(new_messages)

                    self.telegram_bot.send_msg(msg_to_send)

                except Exception as e:
                    logging.info(f'[{dt.datetime.now().isoformat()}] Error parsing chat '
                                 + usernames[chat_number] + ': ' + str(e))
        except Exception as e:
            logging.info(f'[{dt.datetime.now().isoformat()}] Error parsing chats: ' + str(e))

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


    def test_parse_active_orders():
        bot.active_orders()
        input()


    def test_parse_new_messages():
        while True:
            m = input(':')
            if m == 'stop':
                break
            print()

            bot.parse_messages()


    def test_change_order():

        order = Order(
            region='us',
            server='Classic - Smolderweb',
            faction='Horde',
            stock=1523,
            currency='USD',
            description='test',
            min_unit_per_order=532,
            duration=3,
            delivery_option='Face to face trade, Mail, Auction House',
            online_hrs=2,
            offline_hrs=6,
            listing_number=4198011,
            price=0.888888
        )

        bot.change_order(order)


    def test_activation():
        bot.activate_all()
        input()
        bot.deactivate_all()

    test_activation()
    time.sleep(5)
    bot.close()
