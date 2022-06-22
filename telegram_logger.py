from telegram import Bot
import logging


class MyLogsHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET, telegram_token=None, chat_id=None):
        self.bot = Bot(telegram_token)
        self.chat_id = chat_id
        super().__init__(level=level)

    def emit(self, record):
        self.log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=self.log_entry)
