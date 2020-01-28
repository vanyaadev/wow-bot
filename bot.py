
from selenium.webdriver import Chrome
from settings import Settings

import os
import time


def click(driver: Chrome, element):
    driver.execute_script("arguments[0].click()", element)

class Bot:

    def __init__(self, settings: Settings):
        self.settings = settings
        self.driver = Chrome(executable_path=os.getcwd()+'/chromedriver.exe')

    def authorize(self, login, password):
        self.driver.get('https://www.shasso.com/sso/login?action=login')
        self.driver.find_element_by_id('loginform-customers_email_address').send_keys(login)
        self.driver.find_element_by_id('loginform-customers_password').send_keys(password)

        time.sleep(0.5)
        click(self.driver, self.driver.find_element_by_xpath("//button[text()='Login']"))

    def close(self):
        self.driver.close()


if __name__ == '__main__':
    bot = Bot()
    bot.authorize('funnypig1606@gmail.com', 'zaqzaq')
    input()
    bot.close()