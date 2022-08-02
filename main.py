import json
import logging
import os

import redis

from textwrap import dedent
from telegram_logger import MyLogsHandler
from dotenv import load_dotenv
from motlin_api import get_cart, add_item_to_cart, get_access_token, get_product_data
from motlin_api import delete_cart_item, add_order_to_crm, download_product_picture
from telegram_markup import generate_menu_markup, generate_product_markup, generate_cart_markup
from telegram import InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

logger = logging.getLogger('TG ElasticPath Bot')


def send_user_cart(bot, query, access_token):
    chat_id = query.message.chat_id
    cart = get_cart(chat_id, access_token)
    message = ''

    for product in cart['data']:
        product_name = product['name']
        product_description = product['description']
        product_quantity = product['quantity']
        product_total_price = product['meta']['display_price']['with_tax']['value']['formatted']

        message += dedent(f'''{product_name}\n{product_description}
                   {product_quantity}kg for {product_total_price}\n\n''')

    total_price = cart['meta']['display_price']['with_tax']['formatted']
    message += f'Total price: {total_price}'

    reply_markup = InlineKeyboardMarkup(generate_cart_markup(cart))

    bot.send_message(text=message,
                     chat_id=chat_id,
                     reply_markup=reply_markup)

    bot.delete_message(chat_id=query.message.chat_id,
                       message_id=query.message.message_id)

    return 'HANDLE_CART'


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('DATABASE_PASSWORD')
        database_host = os.getenv('DATABASE_HOST')
        database_port = os.getenv('DATABASE_PORT')
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def start(bot, update, access_token):
    reply_markup = InlineKeyboardMarkup(generate_menu_markup(access_token))
    update.message.reply_text('Please choose product:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_description(bot, update, access_token):
    query = update.callback_query

    if json.loads(query.data)['action'] == 'go_back':
        reply_markup = InlineKeyboardMarkup(generate_menu_markup(access_token))

        bot.send_message(text='Please choose product:',
                         chat_id=query.message.chat_id,
                         reply_markup=reply_markup)

        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)

        return 'HANDLE_MENU'

    if json.loads(query.data)['action'] == 'add_to_cart':
        product_sku = json.loads(query.data)['sku']
        quantity = json.loads(query.data)['quantity']

        add_item_to_cart(product_sku, quantity, query.message.chat_id, access_token)
        return 'HANDLE_DESCRIPTION'


def handle_menu(bot, update, access_token):
    query = update.callback_query
    if query.data == 'cart':
        send_user_cart(bot, query, access_token)
        return 'HANDLE_CART'
    else:
        product_response = get_product_data(query, access_token)

        product_sku = product_response['sku']
        product_name = product_response['name']
        product_description = product_response['description']
        product_price = product_response['meta']['display_price']['with_tax']['formatted']
        product_image_id = product_response['relationships']['main_image']['data']['id']

        download_product_picture(product_image_id, access_token)

        reply_markup = generate_product_markup(product_sku)

        caption = f'''Product info:\n\n{product_name}\n\n{product_description}
                                \n{product_price} per kg'''

        with open(f'pictures/{product_image_id}.jpeg', 'rb') as photo:
            bot.send_photo(caption=caption,
                           chat_id=query.message.chat_id,
                           photo=photo,
                           reply_markup=reply_markup,
                           )

        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)

        return 'HANDLE_DESCRIPTION'


def handle_cart(bot, update, access_token):
    query = update.callback_query

    if json.loads(query.data)['action'] == 'go_back':
        reply_markup = InlineKeyboardMarkup(generate_menu_markup(access_token))

        bot.send_message(text='Please choose product:',
                         chat_id=query.message.chat_id,
                         reply_markup=reply_markup)

        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)
        return 'HANDLE_MENU'
    if json.loads(query.data)['action'] == 'pay':
        bot.send_message(text='Please send you email:',
                         chat_id=query.message.chat_id, )

        bot.delete_message(chat_id=query.message.chat_id,
                           message_id=query.message.message_id)

        return 'WAITING_EMAIL'

    if json.loads(query.data)['action'] == 'del':
        delete_cart_item(bot, query, access_token)
        send_user_cart(bot, query, access_token)
        return 'HANDLE_CART'


def handle_waiting_email(bot, update, access_token):
    add_order_to_crm(update.message.chat_id, update.message.text, access_token)

    bot.send_message(text=f'''You have sent the email: {update.message.text}
                            \nFor new order click /start''',
                     chat_id=update.message.chat_id)

    bot.delete_message(chat_id=update.message.chat_id,
                       message_id=update.message.message_id)

    return 'START'


def handle_users_reply(bot, update):
    access_token = get_access_token(ep_client_id, ep_client_secret)

    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_waiting_email
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(bot, update, access_token)
        db.set(chat_id, next_state)
    except Exception as err:
        logger.error(err)


if __name__ == '__main__':
    load_dotenv()
    _database = None
    ep_store_id = os.getenv('EP_STORE_ID')
    ep_client_id = os.getenv('EP_CLIENT_ID')
    ep_client_secret = os.getenv('EP_CLIENT_SECRET')
    telegram_api_key = os.getenv('TELEGRAM_API_KEY')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    my_log_handler = MyLogsHandler(level=logging.DEBUG, telegram_token=telegram_api_key,
                                   chat_id=telegram_chat_id)
    logging.basicConfig(level=20)
    logger.addHandler(my_log_handler)

    updater = Updater(telegram_api_key)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    try:
        logger.warning('Bot TG is working')
        updater.start_polling()
    except Exception as err:
        logger.exception('Bot TG got an error')
