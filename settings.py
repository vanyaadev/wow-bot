
import json

class Settings:

    def __init__(self):
        self.change_order_time = 0                  # type: int
        self.delivery_time = 0                      # type: int
        self.ignore_nicknames = []                  # type: list[str]
        self.ignore_gold_amount = 0                 # type: int
        self.gold_amount = 0                        # type: int
        self.gold_amount_22 = 0                      # type: int
        self.ignore_sellers_by_delivery = 10**12    # type: int
        self.ignore_sellers_by_level = 0            # type: float
        self.ignore_sellers_by_min_price = 10**12   # type: float

    def set_val(self, param, value):
        if param in self.__dict__:
            self.__setattr__(param, value)

    def get_value(self, param):
        if param in self.__dict__:
            return self.__getattribute__(param)

    def save(self, key):
        with open('settings.txt', 'r', encoding='utf-8') as file:
            settings = json.loads(file.read())

        settings[key] = self.__dict__

        with open('settings.txt', 'w', encoding='utf-8') as file:
            file.write(json.dumps(settings))