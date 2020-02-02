
from bot import Bot
import telegram_bot

from threading import Thread


class Dispatcher(Thread):
    def __init__(self):
        super().__init__()

        self.bot = Bot()