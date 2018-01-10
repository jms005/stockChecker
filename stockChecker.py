#!/usr/bin/env python3
# Retrieve stock (securities) price updates and text the results
# to the user.  Intended to be run by cron.
#
# User info and stock ticker symbols stored in local ~/stocklist.json file
# Requires API key for Alpha Vantage (https://www.alphavantage.co/support/)
# which is read from a local alphavantage.json file.

import logging, os, sys, requests, json, re
from datetime import datetime
from twilio.rest import Client

DEBUG = False
logging.basicConfig(level=logging.WARN, format=' %(asctime)s - %(levelname)s - %(message)s')
reg_datetime = re.compile('\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')
global_config = os.getcwd() + '/config.json'
debug_datafile = os.getcwd() + '/debugdata.dat'


def load_user_config(user_config_file='~/stocklist.json'):
    user_config_file = os.path.expanduser(user_config_file)
    if os.path.isfile(user_config_file):
        logging.debug('Reading user_config_file from %s' % user_config_file)
        with open(user_config_file) as fs:
            json_config = json.load(fs)
        return json_config
    else:
        logging.error("Missing user_config_file file %s" % user_config_file)
        return None


def get_app_config(key):
    try:
        with open(global_config) as fs:
            return json.load(fs)[key]
    except Exception as exc:
        logging.critical('Failed to open {}: {}'.format(global_config, exc))


def get_stock_price(series, date):
    logging.debug('Getting price info for {} from {}'.format(date, series))
    price_update = {}

    series_dates = sorted(series.keys())
    previous_update = series_dates[series_dates.index(date) - 1]
    logging.debug('Previous date: {} @ {}'.format(previous_update, series[previous_update]['4. close']))

    price_update['price'] = float(series[date]['4. close'])
    price_update['change'] = (price_update['price'] - float(series[previous_update]['4. close']))
    price_update['change_pct'] = (price_update['change'] / price_update['price']) * 100
    logging.debug('Price: {}\tChange: {}\tPct:{}'.format(price_update['price'], price_update['change'],
                                                         price_update['change_pct']))
    return price_update


def get_stock_updates(tickers='CSCO'):
    av_config = get_app_config('alphavantage')
    results = {}

    logging.debug('Tickers to process: %s' % tickers)
    for ticker in tickers:
        ticker_update = {}

        if not DEBUG:
            api_params = {
                            "function": "TIME_SERIES_DAILY",
                            "symbol": ticker,
                            "datatype": "json",
                            "outputsize": "compact",
                            "apikey": av_config['key']
                        }
            res = requests.get(av_config['api_url'], params=api_params)
            try:
                res.raise_for_status()
            except Exception as exc:
                logging.error("Failed to retrieve stock updates: %s" % exc)
                return None
            json_result = json.loads(res.text)
        else:
            # Test data (end-of-day)
            with open(debug_datafile) as fs:
                json_result = json.load(fs)

        ticker_update['metadata'] = json_result['Meta Data']
        last_refreshed = ticker_update['metadata']['3. Last Refreshed']
        if reg_datetime.match(last_refreshed):
            update_dt = datetime.strptime(last_refreshed, '%Y-%m-%d %H:%M:%S')
        else:
            update_dt = datetime.strptime(last_refreshed, '%Y-%m-%d')
        update_date = update_dt.strftime('%Y-%m-%d')

        ticker_update['last'] = get_stock_price(json_result['Time Series (Daily)'], update_date)
        results[ticker] = ticker_update
        logging.debug('Update: %s = %s' % (ticker, results[ticker]))

    return results


def send_notification(user_address, tickers):
        msg_body = ''
        header = None

        for ticker in sorted(tickers.keys()):
            if not header:
                msg_body += 'Update: ' + tickers[ticker]['metadata']['3. Last Refreshed'] + '\n'
                header = True

            close_price = tickers[ticker]['last']['price']
            close_change = tickers[ticker]['last']['change']
            change_pct = tickers[ticker]['last']['change_pct']
            msg_body += ('{}  ${:.2f},  {:+.2f} ({:+.2f}%)\n'.format(ticker, close_price, close_change, change_pct))

        logging.debug('New message: %s' % msg_body)

        twilio_config = get_app_config('twilio')
        logging.debug('Twilio config: {}'.format(twilio_config))

        if twilio_config and all([twilio_config['phoneNo'], twilio_config['auth'], twilio_config['sid']]):
            t_client = Client(twilio_config['sid'], twilio_config['auth'])
            if not DEBUG:
                try:
                    msg = t_client.messages.create(to=user_address, from_=twilio_config['phoneNo'], body=msg_body)
                    logging.debug('Message SID: {}'.format(msg.sid))
                except Exception as exc:
                    logging.error('Message send failed: {}'.format(exc))
            else:
                logging.debug('Twilio Client: {}'.format(t_client))
        else:
            logging.error("Missing Twilio config in {}".format(global_config))
            return False


def main():
    user_config = load_user_config()
    logging.debug('Config: %s' % user_config)

    if user_config:
        stock_update = get_stock_updates(user_config['tickers'])
        if stock_update:
            send_notification(user_config['user'], stock_update)
        else:
            logging.debug('No stock update available.')
    else:
        pass


# Check for CLI parameter 'DEBUG'
if len(sys.argv) > 1:
    DEBUG = True

if __name__ == "__main__":
    main()
