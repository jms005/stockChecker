#!/usr/bin/env python3
# Retrieve stock (securities) price updates and text the results
# to the user.  Intended to be run by cron.
#
# User info and stock ticker symbols stored in local ~/stocklist.json file
# Requires API key for Alpha Vantage (https://www.alphavantage.co/support/)
# which is read from a local alphavantage.json file.

import logging, os, datetime
import requests,json
from twilio.rest import Client
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')

def loadConfig(config_file='~/stocklist.json'):
    config_file = os.path.expanduser(config_file)

    if os.path.isfile(config_file):
        logging.debug('Reading config_file from %s' % config_file)
        with open(config_file) as fs:
            jsonConfig = json.load(fs)
        return jsonConfig
    else:
        logging.info("Missing config_file file %s" % config_file)
        return None

def get_av_key():
    key_file = 'alphavantage.json'
    with open(key_file) as fs:
        return json.load(fs)['key']

def get_twilio_config():
    config_file = 'twilio.json'
    with open(config_file) as fs:
        config = json.load(fs)
        return config['phoneNo'], config['sid'], config['auth']

def get_stock_updates(tickers='CSCO'):
    api_url = 'https://www.alphavantage.co/query'
    site_key = get_av_key()
    results = {}

    logging.debug('Tickers to process: %s' % tickers)
    for ticker in tickers:
        ticker_update = {}
        parameters = {"function": "TIME_SERIES_DAILY",
                      "symbol": ticker,
                      "datatype": "json",
                      "outputsize": "compact",
                      "apikey": site_key}

        logging.debug('Retrieving: %s ' % parameters)
        res = requests.get(api_url, params=parameters)
        try:
            res.raise_for_status()
        except Exception as exc:
            logging.debug("Failed to retrieve stock updates: %s" % exc)

        json_result = json.loads(res.text)
        logging.debug("Server response: %s" % json_result)

        ticker_update['metadata'] = json_result['Meta Data']
        last_update = ticker_update['metadata']['3. Last Refreshed']
        ticker_update['last'] = json_result['Time Series (Daily)'][last_update]

        results[ticker] = ticker_update
        logging.debug('Update: %s = %s' % (ticker, results[ticker]))

    return results

def send_notification(user_address, tickers):
    twilio_phone, twilio_sid, twilio_auth = get_twilio_config()

    t_client = Client(twilio_sid, twilio_auth)
    if all([twilio_phone, twilio_auth, twilio_sid]):
        msg_body = ''
        header = None

        for ticker in tickers:
            if not header:
                msg_body += 'Update: ' + tickers[ticker]['metadata']['3. Last Refreshed'] + '\n'
            logging.debug('Update message for %s' % ticker)
            close_price = float(tickers[ticker]['last']['4. close'])
            close_change = 'nil'
            # update_time = tickers[ticker]['metadata']['3. Last Refreshed']
            msg_body += ('%s close: $%.2f change: %s\n' % (ticker,close_price,close_change))
        logging.debug('New message: %s' % msg_body)
        msg = t_client.messages.create(to=user_address, from_=twilio_phone, body=msg_body)

        print(msg.sid)

user_config = loadConfig()
logging.debug('Config: %s' % user_config)


if user_config:
    stock_update = get_stock_updates(user_config['tickers'])
    logging.debug('*** Received Updates: \n%s' % stock_update)
    send_notification(user_config['user'], stock_update)
else:
    pass
