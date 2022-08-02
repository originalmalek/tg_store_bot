from motlin_api import get_products
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def generate_menu_markup(access_token):
	products = get_products(access_token)
	markup = []

	for product in products['data']:
		markup.append([InlineKeyboardButton(product['name'], callback_data=product['id'])])
	markup.append([InlineKeyboardButton('CART 🛒', callback_data='cart')])
	return markup


def generate_product_markup(product_sku):
	back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
	add_to_cart_keyboard = []
	for quantity in [1, 5, 10]:
		callback_data = str({"action": "add_to_cart", "sku": product_sku, "quantity": quantity}).replace("'", '"')
		add_to_cart_keyboard.append(InlineKeyboardButton(f"{quantity}kg",
		                                                 callback_data=callback_data))
	keyboard = [add_to_cart_keyboard, back_button]

	return InlineKeyboardMarkup(keyboard)


def generate_cart_markup(cart):
  delete_from_cart_keyboard = []

	for product in cart['data']:
		product_name = product['name']
		product_id = product['id']

		callback_data = str({"action": "del", "id": f"{product_id}"}).replace("'", '"')

		delete_from_cart_keyboard.append([InlineKeyboardButton(f"Delete {product_name}", callback_data=callback_data)])

	back_button = [InlineKeyboardButton("Back", callback_data='{"action": "go_back"}')]
	pay_button = [InlineKeyboardButton("Pay", callback_data='{"action": "pay"}')]
	delete_from_cart_keyboard.append(back_button)
	delete_from_cart_keyboard.append(pay_button)
	keyboard = delete_from_cart_keyboard
	return keyboard
