
import os
import sys
import telepot
from telepot.loop import MessageLoop

AUTH_TOKEN = '981885874:AAEdoPTYiYXC0yv3_BqmqJsRVO5DAZ5Rdjo'

class TelegramBot:
    def __init__(self, auth_token = None):
        if auth_token:
            self.auth_token = auth_token
        else:
            self.auth_token = AUTH_TOKEN
        self.bot = telepot.Bot(self.auth_token)

        if os.path.exists(os.getcwd()+'/chats.txt'):
            with open('chats.txt', 'r') as file:
                self.chats = set(file.read().split('\n'))
        else:
            self.chats = set()

        MessageLoop(self.bot,  {'chat': self.on_msg}).run_as_thread()

    def send_msg(self, msg, chat_id = None):
        try:
            if not chat_id:
                for chat_id in self.chats:
                    if chat_id == '':
                        continue
                    self.bot.sendMessage(chat_id, msg)
            else:
                self.bot.sendMessage(chat_id, msg)
        except Exception as e:
            with open('telegram_error.txt', 'w', encoding='utf-8') as file:
                file.write(str(e)+'\n'*2+str(sys.exc_info()))

    def on_msg(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if not str(chat_id) in self.chats:
            self.chats.add(str(chat_id))
            self.send_msg(f'Your chat id: {chat_id}', chat_id)

            with open('chats.txt', 'w', encoding='utf-8') as file:
                file.write('\n'.join(self.chats))


if __name__ == '__main__':
    tb = TelegramBot(AUTH_TOKEN) # @g2g_chat_receiver_bot
    tb.send_msg(input('Message: '))