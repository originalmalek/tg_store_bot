import logging
import json
import os

import requests
import redis

from telegram_logger import MyLogsHandler
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

logger = logging.getLogger('TG ElasticPath Bot')

def add_item_to_cart(product_sku, quantity, chat_id):
    cart_id = chat_id
    headers = {
        'Authorization': access_token,
        'Content-Type': 'application/json',
    }

    json_data = {"data": {"sku": f"{product_sku}", "type": "cart_item", "quantity": quantity}}

    response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=json_data)


def get_cart(bot, query):
    chat_id = query.message.chat_id
    headers = {
        'Authorization': access_token,
    }
    response = requests.get(f'https://api.moltin.com/v2/carts/{chat_id}/items', headers=headers)
    response.raise_for_status()
    response_data = response.json()

    message = ''
    delete_from_cart_keyboard = []
    for product in response_data['data']:
        product_name = product['name']
        product_id = product['id']
        product_description = product['description']
        product_quantity = product['quantity']
        product_total_price = product['meta']['display_price']['with_tax']['value']['formatted']

        message += f'{product_name}\n{product_description}\n' \
                   f'{product_quantity}kg for {product_total_price}\n\n'

        callback_data = str({"action": "del", "id": f"{product_id}"}).replace("'", '"')

        delete_from_cart_keyboard.append([InlineKeyboardButton(f"Delete {product_name}", callback_data=callback_data)])

    total_price = response_data['meta']['display_price']['with_tax']['formatted']
    message += f'Total price: {total_price}'

    back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
    pay_button = [InlineKeyboardButton("Pay", callback_data='{"action": "pay"}')]
    delete_from_cart_keyboard.append(back_button)
    delete_from_cart_keyboard.append(pay_button)
    keyboard = delete_from_cart_keyboard

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.deleteMessage(chat_id=query.message.chat_id,
                      message_id=query.message.message_id)

    bot.send_message(text=message,
                     chat_id=chat_id,
                     reply_markup=reply_markup)

    return 'HANDLE_CART'


def get_products():
    headers = {
        'Authorization': access_token,
    }

    response = requests.get('https://api.moltin.com/v2/products', headers=headers)
    response.raise_for_status()
    return response.json()


def get_access_token():
    data = {
        'client_id': ep_client_id,
        'client_secret': ep_client_secret,
        'grant_type': 'client_credentials',
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_database_connection():

    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = os.getenv("DATABASE_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def generate_markup():
    markup = []

    for product in products['data']:
        markup.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])
    markup.append([InlineKeyboardButton('CART 🛒', callback_data='cart')])
    return markup


def start(bot, update):
    reply_markup = InlineKeyboardMarkup(generate_markup())

    update.message.reply_text('Please choose product:', reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_description(bot, update):
    query = update.callback_query

    if json.loads(query.data)['action'] == 'go_back':
        reply_markup = InlineKeyboardMarkup(generate_markup())

        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        bot.send_message(text='Please choose product:',
                              chat_id=query.message.chat_id,
                              reply_markup=reply_markup)

        return 'HANDLE_MENU'

    if json.loads(query.data)['action'] == 'add_to_cart':
        product_sku = json.loads(query.data)['sku']
        quantity = json.loads(query.data)['quantity']

        add_item_to_cart(product_sku, quantity, query.message.chat_id)
        return 'HANDLE_DESCRIPTION'


def handle_menu(bot, update):
    query = update.callback_query
    if query.data == 'cart':
        get_cart(bot, query)
        return 'HANDLE_CART'
    else:
        headers = {
            'Authorization': access_token,
        }

        product_response = requests.get(f'https://api.moltin.com/v2/products/{query.data}', headers=headers)
        product_response.raise_for_status()
        product_json_data = product_response.json()['data']

        product_sku = product_json_data['sku']

        product_name = product_json_data['name']
        product_description = product_json_data['description']
        product_price = product_json_data['meta']['display_price']['with_tax']['formatted']
        product_image_id = product_json_data['relationships']['main_image']['data']['id']

        image_response = requests.get(f'https://api.moltin.com/v2/files/{product_image_id}', headers=headers)
        image_response.raise_for_status()

        image_url = image_response.json()['data']['link']['href']

        if not os.path.exists(f'pictures/{product_image_id}.jpeg'):
            with open(f'pictures/{product_image_id}.jpeg', 'wb') as f:
                f.write(requests.get(image_url).content)

        back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
        add_to_cart_keyboard = []
        for quantity in [1, 5, 10]:
            callback_data = str({"action": "add_to_cart", "sku": product_sku, "quantity": quantity}).replace("'", '"')
            add_to_cart_keyboard.append(InlineKeyboardButton(f"{quantity}kg",
                                                             callback_data=callback_data))
        keyboard = [add_to_cart_keyboard, back_button]

        reply_markup = InlineKeyboardMarkup(keyboard)

        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        bot.send_photo(caption=f"Product info:\n\n{product_name}\n\n{product_description}"
                               f"\n{product_price} per kg",
                       chat_id=query.message.chat_id,
                       photo=open(f'pictures/{product_image_id}.jpeg', 'rb'),
                       reply_markup=reply_markup)

        return 'HANDLE_DESCRIPTION'


def delete_cart_item(bot, query):
    headers = {
        'Authorization': f'{access_token}',
    }
    product_id = json.loads(query.data)['id']
    response = requests.delete(f'https://api.moltin.com/v2/carts/{query.message.chat_id}/items/{product_id}',
                               headers=headers)
    response.raise_for_status()


def handle_cart(bot, update):
    query = update.callback_query

    if json.loads(query.data)['action'] == 'go_back':
        reply_markup = InlineKeyboardMarkup(generate_markup())

        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        bot.send_message(text='Please choose product:',
                         chat_id=query.message.chat_id,
                         reply_markup=reply_markup)

        return 'HANDLE_MENU'
    if json.loads(query.data)['action'] == 'pay':
        bot.deleteMessage(chat_id=query.message.chat_id,
                          message_id=query.message.message_id)

        bot.send_message(text='Please send you email:',
                         chat_id=query.message.chat_id,)
        return 'WAITING_EMAIL'

    if json.loads(query.data)['action'] == 'del':
        delete_cart_item(bot, query)
        get_cart(bot, query)
        return 'HANDLE_CART'


def add_order_to_crm(chat_id, email):

    headers = {
        'Authorization': access_token,
    }

    json_data = {
        'data': {
            'type': 'customer',
            'name': f'{chat_id}',
            'email': email,
            'password': 'mysecretpassword',
        },
    }

    response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=json_data)
    response.raise_for_status()

    response = requests.get('https://api.moltin.com/v2/customers', headers=headers)
    response.raise_for_status()


def handle_waiting_email(bot, update):

    bot.deleteMessage(chat_id=update.message.chat_id,
                      message_id=update.message.message_id)

    bot.send_message(text=f'You have sent the email: {update.message.text}\n'
                     'For new order click /start',
                     chat_id=update.message.chat_id, )

    add_order_to_crm(update.message.chat_id, update.message.text)

    return 'START'


def handle_users_reply(bot, update):
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
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_waiting_email
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == '__main__':
    load_dotenv()
    _database = None
    ep_store_id = os.getenv('EP_STORE_ID')
    ep_client_id = os.getenv('EP_CLIENT_ID')
    ep_client_secret = os.getenv('EP_CLIENT_SECRET')
    telegram_api_key = os.getenv('TELEGRAM_API_KEY')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    access_token = get_access_token()

    my_log_handler = MyLogsHandler(level=logging.DEBUG, telegram_token=telegram_api_key,
                                   chat_id=telegram_chat_id)
    logging.basicConfig(level=20)
    logger.addHandler(my_log_handler)

    products = get_products()

    updater = Updater(telegram_api_key)
    dispatcher = updater.dispatcher


    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))

    try:
        logger.warning('Bot TG is working')
        updater.start_polling()
    except Exception as err:
        logger.error('Bot TG got an error')
        logger.error(err, exc_info=True)
