import time
import random
import logging
import xlrd

from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.common.by import By
from order import Order

def click(driver: Chrome, element):
    driver.execute_script("arguments[0].click()", element)


def wait_element(driver: Chrome, xpath: str, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, xpath)
            )
        )
    except TimeoutException:
        logging.info(f'[{time.time()}] TimeoutError waiting element by xpath: ' + xpath)

def random_sleep(a=0.1, b=0.2, delay=None):
    if delay:
        a += delay
        b += delay
    time.sleep(random.uniform(a, b))


def enable_download_headless(browser: Chrome, download_dir):
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)


def make_proxy(proxy):
    if proxy.split(',') == 3:
        host_port, user, passw = proxy.split(',')
        proxy = {
            'http': f'http://{user}:{passw}@{host_port}',
            'https': f'http://{user}:{passw}@{host_port}'
        }
    else:
        proxy = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }

    return proxy


def orders_from_excel(file_path, just_active=False):

    orders = []

    wb = xlrd.open_workbook(file_path)
    sh = wb.sheet_by_index(0)

    region = 'eu' if 'eu' in sh.cell_value(0, 0).lower() else 'us'

    row = 9  # 10
    while True:
        try:
            if sh.cell_value(row, 0) == xlrd.empty_cell.value:
                break
        except IndexError:
            break

        listing_number = int(sh.cell_value(row, 0))
        server = sh.cell_value(row, 1)
        faction = sh.cell_value(row, 2)
        currency = sh.cell_value(row, 3)
        price = float(sh.cell_value(row, 4))
        description = sh.cell_value(row, 5)
        stock = int(sh.cell_value(row, 6))
        min_unit_per_order = int(sh.cell_value(row, 7))
        duration = int(sh.cell_value(row, 8))
        delivery_option = sh.cell_value(row, 9)
        online_hrs = int(sh.cell_value(row, 10))
        offline_hrs = int(sh.cell_value(row, 11))
        status = sh.cell_value(row, 12)

        if just_active and status != 'Active':
            row += 1
            continue

        order = Order(region=region,
                      server=server,
                      faction=faction,
                      stock=stock,
                      currency=currency,
                      description=description,
                      min_unit_per_order=min_unit_per_order,
                      duration=duration,
                      delivery_option=delivery_option,
                      online_hrs=online_hrs,
                      offline_hrs=offline_hrs,
                      price=price,
                      listing_number=listing_number,
                      status=status)

        orders.append(order)
        row += 1

    return orders


if __name__ == '__main__':
    print(make_proxy('123.123.123.123:8080,MyLogin,MyPassword'))