import json
import os

import requests

from datetime import timedelta, datetime

EP_ACCESS_TOKEN = None
EP_TOKEN_TIME = None


def get_cart(chat_id, access_token):
	headers = {
		'Authorization': access_token,
	}
	response = requests.get(f'https://api.moltin.com/v2/carts/{chat_id}/items', headers=headers)
	response.raise_for_status()
	return response.json()


def get_products(access_token):
	headers = {
		'Authorization': access_token,
	}

	response = requests.get('https://api.moltin.com/v2/products', headers=headers)
	response.raise_for_status()
	return response.json()


def add_item_to_cart(product_sku, quantity, chat_id, access_token):
	cart_id = chat_id
	headers = {
		'Authorization': access_token,
		'Content-Type': 'application/json',
	}

	json_data = {"data": {"sku": f"{product_sku}", "type": "cart_item", "quantity": quantity}}

	response = requests.post(f'https://api.moltin.com/v2/carts/{cart_id}/items', headers=headers, json=json_data)
	response.raise_for_status()
	return response.json()


def get_access_token(ep_client_id, ep_client_secret):
	global EP_ACCESS_TOKEN
	global EP_TOKEN_TIME

	if not EP_ACCESS_TOKEN or datetime.now() > EP_TOKEN_TIME + timedelta(minutes=59):
		data = {
			'client_id': ep_client_id,
			'client_secret': ep_client_secret,
			'grant_type': 'client_credentials',
		}

		response = requests.post('https://api.moltin.com/oauth/access_token', data=data)
		response.raise_for_status()
		EP_ACCESS_TOKEN = response.json()['access_token']
		EP_TOKEN_TIME = datetime.now()
	return EP_ACCESS_TOKEN


def delete_cart_item(bot, query, access_token):
	headers = {
		'Authorization': access_token,
	}
	product_id = json.loads(query.data)['id']
	response = requests.delete(f'https://api.moltin.com/v2/carts/{query.message.chat_id}/items/{product_id}',
	                           headers=headers)
	response.raise_for_status()
	return response.json()


def add_order_to_crm(chat_id, email, access_token):
	headers = {
		'Authorization': access_token,
	}

	json_data = {
		'data': {
			'type': 'customer',
			'name': str(chat_id),
			'email': email,
			'password': 'mysecretpassword',
		},
	}

	response = requests.post('https://api.moltin.com/v2/customers', headers=headers, json=json_data)
	response.raise_for_status()


def get_product_data(query, access_token):
	headers = {
		'Authorization': access_token,
	}
	product_response = requests.get(f'https://api.moltin.com/v2/products/{query.data}', headers=headers)
	product_response.raise_for_status()
	return product_response.json()['data']


def download_product_picture(product_image_id, access_token):
	headers = {
		'Authorization': access_token,
	}
	image_response = requests.get(f'https://api.moltin.com/v2/files/{product_image_id}', headers=headers)
	image_response.raise_for_status()

	image_url = image_response.json()['data']['link']['href']

	if not os.path.exists(f'pictures/{product_image_id}.jpeg'):
		with open(f'pictures/{product_image_id}.jpeg', 'wb') as f:
			f.write(requests.get(image_url).content) 

			
