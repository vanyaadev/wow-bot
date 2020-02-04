
import time
import logging
import datetime as dt

from threading import Thread

from bot import Bot
from settings import Settings
from parser import GItem, GoldParser, make_url
from utils import make_proxy


class Dispatcher(Thread):
    def __init__(self,
                 classic_settings: Settings,
                 bfa_settings: Settings):

        super().__init__()

        self.bot = Bot()

        self.classic_settings = classic_settings
        self.bfa_settings = bfa_settings

        self.classic_last_update = 0
        self.bfa_last_update = 0

        self.killed = False
        self.paused = False
        self.pause_accepted = False

        self.proxy_list = []
        with open('proxy_list.txt', 'r', encoding='utf-8') as file:
            for line in file.read().split('\n'):
                if line.strip() == '':
                    continue
                self.proxy_list.append(make_proxy(line))

    # Run

    def run(self):
        while not self.killed:
            logging.info(f'[{dt.datetime.now().isoformat()}] New cycle started')

            self.active_orders_eu = self.bot.active_orders('eu')    # type: list[Order]
            self.active_orders_us = self.bot.active_orders('us')    # type: list[Order]

            self.parse_items_prices()

            self.process_orders()

            while self.paused:  # wait for unpause
                self.pause_accepted = True
                time.sleep(0.5)

            self.pause_accepted = False

    # Process items methods

    def parse_items_prices(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Parse items prices started')

        servers_to_parse_eu_horde = set()
        servers_to_parse_eu_alliance = set()
        servers_to_parse_us_horde = set()
        servers_to_parse_us_alliance = set()
        for ao in self.active_orders_eu:
            (servers_to_parse_eu_horde
             if ao.faction.lower() == 'horde'
             else servers_to_parse_eu_alliance).add(ao.server)
        for ao in self.active_orders_us:
            (servers_to_parse_us_horde
             if ao.faction.lower() == 'horde'
             else servers_to_parse_us_alliance).add(ao.server)

        number_of_parsers = len(servers_to_parse_eu_alliance) + len(servers_to_parse_eu_horde) + \
                            len(servers_to_parse_us_alliance) + len(servers_to_parse_us_horde)
        if len(self.proxy_list) == 0:
            proxy_iter = iter([None] * number_of_parsers)
        else:
            proxy_iter = iter(self.proxy_list * (number_of_parsers // len(self.proxy_list) + 1))

        eu_horde_parsers = [GoldParser(make_url('eu', server, 'Horde'),    next(proxy_iter))
                            for server in servers_to_parse_eu_horde]
        eu_allia_parsers = [GoldParser(make_url('eu', server, 'Alliance'), next(proxy_iter))
                            for server in servers_to_parse_eu_alliance]
        us_horde_parsers = [GoldParser(make_url('us', server, 'Horde'),    next(proxy_iter))
                            for server in servers_to_parse_us_horde]
        us_allia_parsers = [GoldParser(make_url('us', server, 'Alliance'), next(proxy_iter))
                            for server in servers_to_parse_us_alliance]

        gold_parsers = eu_horde_parsers + eu_allia_parsers + us_horde_parsers + us_allia_parsers

        for gp in gold_parsers:
            gp.start()
            time.sleep(1)

        for gp in gold_parsers:
            gp.join()

        self.eu_horde_items = []
        for ehp in eu_horde_parsers:
            self.eu_horde_items.extend(self.filter_items(ehp.result))
        self.eu_horde_items.sort(key=lambda item: item.price)

        self.eu_alliance_items = []
        for eap in eu_allia_parsers:
            self.eu_alliance_items.extend(self.filter_items(eap.result))
        self.eu_alliance_items.sort(key=lambda item: item.price)

        self.us_horde_items = []
        for uhp in us_horde_parsers:
            self.us_horde_items.extend(self.filter_items(uhp.result))
        self.us_horde_items.sort(key=lambda item: item.price)

        self.us_alliance_items = []
        for uap in us_allia_parsers:
            self.us_alliance_items.extend(self.filter_items(uap.result))
        self.us_alliance_items.sort(key=lambda item: item.price)

        logging.info(f'[{dt.datetime.now().isoformat()}] Parse items prices finished')

    def filter_items(self, items: list[GItem]):
        logging.info(f'[{dt.datetime.now().isoformat()}] Filtering parsed items')

        filtered_items = []

        for item in items:
            settings = self.classic_settings if 'classic' in item.server else self.bfa_settings

            if item.seller_name in settings.ignore_nicknames:
                continue
            if item.delivery_time > settings.delivery_time:
                continue
            if item.min_quantity * item.price > settings.ignore_sellers_by_min_price:
                continue
            if item.seller_rating < settings.ignore_sellers_by_level:
                continue
            if item.stock_amount < settings.ignore_gold_amount:
                continue

            filtered_items.append(item)

        return filtered_items

    def get_items_by_server(self, region, faction, server):
        items = self.__getattribute__(f'{region.lower()}_{faction.lower()}_items') #  type: list[GItem]

        return [item for item in items if item.server == server]


    # Process orders methods

    def process_classic_orders(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Process orders started')

        for order in self.active_orders_eu:
            logging.info(f'[{dt.datetime.now().isoformat()}] Take order: #{order.listing_number}')

            settings = self.classic_settings if 'classic' in order.server.lower() else self.bfa_settings
            items = self.get_items_by_server('eu', order.faction, order.server)
            # take first 5 items

            # STEP 1
            sellers_gold = [i.stock_amount <= settings.gold_amount for i in items[:5]]
            all_gold_is_less_than = all(sellers_gold)
            just_one_more_than = items[0].stock_amount > settings.gold_amount and all(sellers_gold[1:])

            # STEP 2
            if all_gold_is_less_than:
                percent_difference = lambda p1, p2: p1 / p2 - 1

                compare_percent_difference = [
                    [percent_difference(items[i].price, items[j].price)] for i in range(5) for j in range(5)
                ]

                # 2.1
                if all(perc_dif > 0.02 for row in compare_percent_difference for perc_dif in row):
                    



    # Manage thread methods

    def kill(self):
        self.killed = True

    def pause(self):
        self.paused = not self.paused
