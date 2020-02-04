import time
import random
from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By


def click(driver: Chrome, element):
    driver.execute_script("arguments[0].click()", element)


def wait_element(driver: Chrome, xpath: str, timeout=10):
    WebDriverWait(driver, timeout).until(
        expected_conditions.presence_of_element_located(
            (By.XPATH, xpath)
        )
    )


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


if __name__ == '__main__':
    print(make_proxy('123.123.123.123:8080,MyLogin,MyPassword'))