from selenium.webdriver import Chrome
from time import sleep

def parse_chat_history(username_credentials, password_credentials):
    webdriver = "../nba-stats-bot/chromedriver.exe"
    driver = Chrome(webdriver)
    driver.get('https://www.g2g.com/sso/login?next_url=https%3A%2F%2Fwww.g2g.com%2F')

    username = '//*[@id="loginform-customers_email_address"]'
    passord = '//*[@id="loginform-customers_password"]'
    login_button = '//*[@id="w0"]/div[6]/div/button'

    driver.find_element_by_xpath(username).send_keys(username_credentials)
    driver.find_element_by_xpath(passord).send_keys(password_credentials)
    driver.find_element_by_xpath(login_button).click()

parse_chat_history('detskov5@gmail.com','Detskov5')
sleep(10)