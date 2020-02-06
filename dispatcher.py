import os
import sys
import time
import logging
import datetime as dt

from threading import Thread

from bot import Bot
from settings import Settings
from parser_items import GItem, GoldParser, make_url
from utils import make_proxy, orders_from_excel, add_change_orders_from_excel

PRICE_STEP = 0.00001


class Dispatcher(Thread):
    def __init__(self,
                 classic_settings: Settings,
                 bfa_settings: Settings):

        super().__init__()

        self.bot = Bot()

        self.classic_settings = classic_settings
        self.bfa_settings = bfa_settings

        self.classic_orders_last_update = 0
        self.bfa_orders_last_update = 0

        self.skip_classic = False
        self.skip_bfa = False

        self.classic_last_update = 0
        self.bfa_last_update = 0

        self.killed = False
        self.paused = True
        self.pause_accepted = False

        self.proxy_list = []

        if os.path.exists('proxy_list.txt'):
            with open('proxy_list.txt', 'r', encoding='utf-8') as file:
                for line in file.read().split('\n'):
                    if line.strip() == '':
                        continue
                    self.proxy_list.append(make_proxy(line))


    # Run

    def run(self):
        while not self.killed:
            while self.paused:  # wait for unpause
                self.pause_accepted = True
                time.sleep(0.5)

            self.pause_accepted = False

            # Accept commands from gui

            if time.time() - self.classic_last_update > self.classic_settings.change_order_time * 60:
                self.skip_classic = False

            if time.time() - self.bfa_last_update > self.bfa_settings.change_order_time * 60:
                self.skip_bfa = False

            if self.skip_bfa and self.skip_classic:
                time.sleep(1)
                continue

            # Work
            logging.info(f'[{dt.datetime.now().isoformat()}] New cycle started')

            self.active_orders_eu = self.bot.active_orders('eu')    # type: list[Order]
            self.active_orders_us = self.bot.active_orders('us')    # type: list[Order]

            self.parse_items_prices()

            changed_orders = self.process_orders() # type: set[Order]
            for order in changed_orders:
                self.bot.change_order(order)

            if any(['classic' in o.server.lower() for o in changed_orders]):
                self.classic_last_update = time.time()
            if any(['classic' not in o.server.lower() for o in changed_orders]):
                self.bfa_last_update = time.time()

            time.sleep(1)

    # Process items methods

    def parse_items_prices(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Parse items prices started')

        servers_to_parse_eu_horde = set()
        servers_to_parse_eu_alliance = set()
        servers_to_parse_us_horde = set()
        servers_to_parse_us_alliance = set()
        for ao in self.active_orders_eu:
            if self.skip_classic and 'classic' in ao.server.lower():
                continue
            if self.skip_bfa and 'classic' not in ao.server.lower():
                continue

            (servers_to_parse_eu_horde
             if ao.faction.lower() == 'horde'
             else servers_to_parse_eu_alliance).add(ao.server)
        for ao in self.active_orders_us:
            if self.skip_classic and 'classic' in ao.server.lower():
                continue
            if self.skip_bfa and 'classic' not in ao.server.lower():
                continue

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

    def filter_items(self, items: list):
        items = items # type: list[GItem]
        logging.info(f'[{dt.datetime.now().isoformat()}] Filtering parsed items')

        filtered_items = []

        for item in items:
            settings = self.classic_settings if 'classic' in item.server else self.bfa_settings

            if item.seller_name in settings.ignore_nicknames:
                continue
            if item.delivery_time > settings.ignore_sellers_by_delivery:
                continue
            if item.min_quantity * item.price > settings.ignore_sellers_by_min_price:
                continue
            if item.seller_professional_level < settings.ignore_sellers_by_level:
                continue
            if item.stock_amount < settings.ignore_gold_amount:
                continue

            filtered_items.append(item)

        return filtered_items

    def get_items_by_server(self, region, faction, server):
        items = self.__getattribute__(f'{region.lower()}_{faction.lower()}_items') #  type: list[GItem]

        return [item for item in items if item.server == server]

    # Process orders methods

    def process_orders(self):
        logging.info(f'[{dt.datetime.now().isoformat()}] Process orders started')

        changed_orders = []

        for order in self.active_orders_eu + self.active_orders_us:

            try:
                logging.info(f'[{dt.datetime.now().isoformat()}] Take order: #{order.listing_number}')
                SELECTED_PRICE = None

                settings = self.classic_settings if 'classic' in order.server.lower() else self.bfa_settings
                items = self.get_items_by_server(order.region, order.faction, order.server)
                # take first 5 items

                # STEP 1
                sellers_gold = [i.stock_amount <= settings.gold_amount for i in items[:5]]
                all_gold_is_less_than = all(sellers_gold)
                just_one_more_than = items[0].stock_amount > settings.gold_amount and all(sellers_gold[1:])

                percent_difference = lambda p1, p2: p1 / p2 - 1
                # STEP 2
                if all_gold_is_less_than:

                    compare_percent_difference = [
                        [percent_difference(items[i].price, items[j].price) for j in range(5)] for i in range(5)
                    ]

                    # 2.1
                    if all(abs(perc_dif) < 0.02 for row in compare_percent_difference for perc_dif in row) and \
                            sum([i.stock_amount for i in items[:5]]) > settings.gold_amount:
                        for i in range(5):
                            if items[i].stock_amount > settings.gold_amount_22:

                                SELECTED_PRICE = items[i].price - PRICE_STEP
                                logging.info(f'[{dt.datetime.now().isoformat()}]'+
                                             f' Order: #{order.listing_number} price {SELECTED_PRICE} selected at step 2.1')
                                break

                    # 2.2
                    if any(perc_dif > 0.02 for row in compare_percent_difference for perc_dif in row) and \
                            sum([i.stock_amount for i in items[:5]]):
                        for i in range(5):
                            for j in range(5):
                                if compare_percent_difference[i][j] > 0.02:
                                    SELECTED_PRICE = (items[i].price + items[j].price) / 2
                                    logging.info(f'[{dt.datetime.now().isoformat()}]' +
                                                 f' Order: #{order.listing_number} price {SELECTED_PRICE} selected at step 2.2')
                                    break

                            if SELECTED_PRICE:
                                break

                # STEP 3
                if just_one_more_than:
                    avr_price = sum([i.price for i in items[2:5]]) / 4
                    perc_diff = percent_difference(avr_price, items[0].price)

                    if perc_diff < 0.07 or \
                        (0.07 <= perc_diff <= 0.12 and
                         items[0].stock_amount > settings.gold_amount * 2 and
                         items[0].seller_professional_level > 100
                        ):

                        SELECTED_PRICE = items[0].price - PRICE_STEP

                        logging.info(f'[{dt.datetime.now().isoformat()}]' +
                                     f' Order: #{order.listing_number} price {SELECTED_PRICE} selected at step 3')

                if SELECTED_PRICE:
                    order.price = round(SELECTED_PRICE, 6)
                    changed_orders.append(order)

            except:
                logging.info(f'[{dt.datetime.now().isoformat()}] Error processing order #{order.listing_number}:' +
                             str(sys.exc_info()[0]))

        return changed_orders

    def activate_all_orders(self):
        self.bot.activate_all()

    def deactivate_all_orders(self):
        self.bot.deactivate_all()

    def add_orders_from_excel(self, fpath):
        orders = add_change_orders_from_excel(fpath)
        active_orders = self.bot.active_orders('eu') + self.bot.active_orders('us')

        logging.info(f'[{dt.datetime.now().isoformat()}] Processing {len(orders)} from Excel')

        for order in orders:
            if order in active_orders:
                logging.info(f'[{dt.datetime.now().isoformat()}] Editing order #{order.listing_number}')
                self.bot.change_order(order)
            else:
                logging.info(f'[{dt.datetime.now().isoformat()}] Adding order to g2g')
                self.bot.add_order(order, order.price)

    # Manage thread methods

    def kill(self):
        self.killed = True

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False
