# Elastic path telegram bot
The project create store from [ElasticPath](https://euwest.cm.elasticpath.com/) in telegram.


## Description
The code: 
The project create store from [ElasticPath](https://euwest.cm.elasticpath.com/) in telegram.

The project use:  
 * [ElasticPath API](https://documentation.elasticpath.com/commerce-cloud/docs/api/);  
 * [Telegram API](https://core.telegram.org/bots/api) with module [pyTelegramBotAPI](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Introduction-to-the-API).
 * [Redis API](https://redis.io/) with module [Redis](https://github.com/redis/redis).



## Requirements
Python==3.8  
requests==2.27.1  
redis==3.2.1  
python-dotenv==0.20.0  
python-telegram-bot===11.1.0  

Create bot on [telegram.org](https://t.me/botfather) ang get API key.  
Create database on [Redis API](https://redis.io/) ang get Database Host, Database Password, Database Port.
Create store in [ElasticPath](https://euwest.cm.elasticpath.com/) ang get Store Id, Client Id, Clinest Secret. 
Create file '.env' and add the code:
```
EP_STORE_ID=your_elasticpath_store_id
EP_CLIENT_ID=your_elasticpath_client_id
EP_CLIENT_SECRET=your_elasticpath_clien_secret
TELEGRAM_API_KEY=your_telegram_api_key
DATABASE_HOST=your_redis_database_host
DATABASE_PASSWORD=your_redis_database_password
DATABASE_PORT=your_redis_database_port
```

Install requirements modules:
```
pip install -r requirements.txt	
```


### How to use

Install requirements.  
Open and run 'main.py'.
```
python main.py	
```

## Project goal

The code was written for educational purpose on online course for Api developers [Devman](http://dvmn.org). 

