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

DEBUG=False
logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
reg_datetime = re.compile('\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}\d{2}')


def load_config(config_file='~/stocklist.json'):
    config_file = os.path.expanduser(config_file)
    if os.path.isfile(config_file):
        logging.debug('Reading config_file from %s' % config_file)
        with open(config_file) as fs:
            json_config = json.load(fs)
        return json_config
    else:
        logging.info("Missing config_file file %s" % config_file)
        return None


# TODO Merge get_av_key and get_twilio_config files into single config file and single function retrieving a list given a string (e.g. 'twilio' or 'av')
def get_av_key():
    key_file = os.getcwd() + '/alphavantage.json'
    with open(key_file) as fs:
        return json.load(fs)['key']

def get_twilio_config():
    config_file = os.getcwd() + '/twilio.json'
    try:
        with open(config_file) as fs:
            config = json.load(fs)
            return config['phoneNo'], config['sid'], config['auth']
    except:
        logging.error('Failed to open {}'.format(config_file))


def get_stock_price(series, date):
    logging.debug('Getting price info for {} from {}'.format(date, series))
    price_update = {}
    series_dates = [*series]

    previous_update = series_dates[series_dates.index(date)+1]

    price_update['price'] = float(series[date]['4. close'])
    price_update['change'] = (price_update['price'] - float(series[previous_update]['4. close']))
    price_update['change_pct'] = (price_update['change'] / price_update['price']) * 100

    logging.debug('Price: {}\tChange: {}\tPct:{}'.format(price_update['price'], price_update['change'],
                                                         price_update['change_pct']))
    return price_update


def get_stock_updates(tickers = 'CSCO'):
    api_url = 'https://www.alphavantage.co/query'
    site_key = get_av_key()
    results = {}

    logging.debug('Tickers to process: %s' % tickers)
    for ticker in tickers:
        ticker_update = {}

        if not DEBUG:
            api_params = {"function": "TIME_SERIES_DAILY",
                      "symbol": ticker,
                      "datatype": "json",
                      "outputsize": "compact",
                      "apikey": site_key}
            res = requests.get(api_url, params=api_params)
            try:
                res.raise_for_status()
            except Exception as exc:
                logging.error("Failed to retrieve stock updates: %s" % exc)
            json_result = json.loads(res.text)
        else:
            # Test data (end-of-day)
            # TODO move test data to separate file
            json_result = {
                'Meta Data': {'1. Information': 'Daily Prices (open, high, low, close) and Volumes', '2. Symbol': 'CSCO',
                              '3. Last Refreshed': '2017-11-30', '4. Output Size': 'Compact', '5. Time Zone': 'US/Eastern'},
                'Time Series (Daily)': {
                    '2017-11-30': {'1. open': '37.6200', '2. high': '37.8000', '3. low': '37.3000', '4. close': '37.3000',
                                   '5. volume': '30742858'},
                    '2017-11-29': {'1. open': '37.7500', '2. high': '38.0250', '3. low': '37.2300', '4. close': '37.4800',
                                   '5. volume': '36723394'},
                    '2017-11-28': {'1. open': '37.0000', '2. high': '37.8000', '3. low': '36.9800', '4. close': '37.7300',
                                   '5. volume': '30097816'},
                    '2017-11-27': {'1. open': '36.5100', '2. high': '37.0900', '3. low': '36.5000', '4. close': '36.8700',
                                   '5. volume': '20667352'},
                    '2017-11-24': {'1. open': '36.4100', '2. high': '36.5700', '3. low': '36.3200', '4. close': '36.4900',
                                   '5. volume': '6155294'},
                    '2017-11-22': {'1. open': '36.7000', '2. high': '36.7200', '3. low': '36.3600', '4. close': '36.4500',
                                   '5. volume': '16650130'},
                    '2017-11-21': {'1. open': '36.7500', '2. high': '36.9700', '3. low': '36.5800', '4. close': '36.6500',
                                   '5. volume': '23986203'},
                    '2017-11-20': {'1. open': '35.9300', '2. high': '36.5400', '3. low': '35.9300', '4. close': '36.5000',
                                   '5. volume': '26376364'},
                    '2017-11-17': {'1. open': '35.9000', '2. high': '36.3200', '3. low': '35.8100', '4. close': '35.9000',
                                   '5. volume': '27106406'},
                    '2017-11-16': {'1. open': '36.0400', '2. high': '36.6700', '3. low': '35.8300', '4. close': '35.8800',
                                   '5. volume': '59861205'},
                    '2017-11-15': {'1. open': '33.9700', '2. high': '34.3100', '3. low': '33.7500', '4. close': '34.1100',
                                   '5. volume': '27797071'},
                    '2017-11-14': {'1. open': '33.8600', '2. high': '34.1600', '3. low': '33.8000', '4. close': '34.0400',
                                   '5. volume': '15540925'},
                    '2017-11-13': {'1. open': '33.8600', '2. high': '34.2100', '3. low': '33.8300', '4. close': '33.9500',
                                   '5. volume': '15608341'},
                    '2017-11-10': {'1. open': '34.0600', '2. high': '34.0900', '3. low': '33.6700', '4. close': '33.9900',
                                   '5. volume': '19003147'},
                    '2017-11-09': {'1. open': '34.2900', '2. high': '34.3200', '3. low': '33.8700', '4. close': '34.0500',
                                   '5. volume': '16266161'},
                    '2017-11-08': {'1. open': '34.3100', '2. high': '34.5000', '3. low': '34.1200', '4. close': '34.5000',
                                   '5. volume': '13061334'},
                    '2017-11-07': {'1. open': '34.3200', '2. high': '34.4800', '3. low': '34.2100', '4. close': '34.4000',
                                   '5. volume': '10980008'},
                    '2017-11-06': {'1. open': '34.3700', '2. high': '34.5600', '3. low': '34.2600', '4. close': '34.4100',
                                   '5. volume': '12725467'},
                    '2017-11-03': {'1. open': '34.2800', '2. high': '34.4900', '3. low': '34.0300', '4. close': '34.4700',
                                   '5. volume': '13293171'},
                    '2017-11-02': {'1. open': '34.5500', '2. high': '34.6400', '3. low': '34.1600', '4. close': '34.2100',
                                   '5. volume': '19647242'},
                    '2017-11-01': {'1. open': '34.2900', '2. high': '34.7500', '3. low': '34.2800', '4. close': '34.6200',
                                   '5. volume': '21831973'},
                    '2017-10-31': {'1. open': '33.9800', '2. high': '34.2400', '3. low': '33.9600', '4. close': '34.1500',
                                   '5. volume': '13544441'},
                    '2017-10-30': {'1. open': '34.1300', '2. high': '34.3800', '3. low': '33.8200', '4. close': '34.0400',
                                   '5. volume': '18241531'},
                    '2017-10-27': {'1. open': '34.1500', '2. high': '34.6200', '3. low': '34.0900', '4. close': '34.4300',
                                   '5. volume': '20237956'},
                    '2017-10-26': {'1. open': '34.4100', '2. high': '34.5100', '3. low': '34.0700', '4. close': '34.2700',
                                   '5. volume': '14541155'},
                    '2017-10-25': {'1. open': '34.7300', '2. high': '34.7300', '3. low': '34.1600', '4. close': '34.3000',
                                   '5. volume': '17012218'},
                    '2017-10-24': {'1. open': '34.4000', '2. high': '34.6700', '3. low': '34.2500', '4. close': '34.5800',
                                   '5. volume': '15273905'},
                    '2017-10-23': {'1. open': '34.4500', '2. high': '34.6800', '3. low': '34.2700', '4. close': '34.3500',
                                   '5. volume': '22490134'},
                    '2017-10-20': {'1. open': '34.0200', '2. high': '34.3900', '3. low': '34.0100', '4. close': '34.2500',
                                   '5. volume': '24055347'},
                    '2017-10-19': {'1. open': '33.5100', '2. high': '33.8900', '3. low': '33.4500', '4. close': '33.7500',
                                   '5. volume': '12928532'},
                    '2017-10-18': {'1. open': '33.7200', '2. high': '33.7500', '3. low': '33.4400', '4. close': '33.5500',
                                   '5. volume': '9739887'},
                    '2017-10-17': {'1. open': '33.5900', '2. high': '33.6700', '3. low': '33.4600', '4. close': '33.6000',
                                   '5. volume': '8633089'},
                    '2017-10-16': {'1. open': '33.6000', '2. high': '33.6400', '3. low': '33.4700', '4. close': '33.5400',
                                   '5. volume': '10469019'},
                    '2017-10-13': {'1. open': '33.4000', '2. high': '33.5700', '3. low': '33.3200', '4. close': '33.4700',
                                   '5. volume': '13451108'},
                    '2017-10-12': {'1. open': '33.2600', '2. high': '33.4600', '3. low': '33.1700', '4. close': '33.2600',
                                   '5. volume': '17811160'},
                    '2017-10-11': {'1. open': '33.3800', '2. high': '33.6300', '3. low': '33.2500', '4. close': '33.5900',
                                   '5. volume': '12353462'},
                    '2017-10-10': {'1. open': '33.8800', '2. high': '33.9100', '3. low': '33.4700', '4. close': '33.5500',
                                   '5. volume': '17978700'},
                    '2017-10-09': {'1. open': '33.7700', '2. high': '33.8900', '3. low': '33.6100', '4. close': '33.7600',
                                   '5. volume': '8684822'},
                    '2017-10-06': {'1. open': '33.6500', '2. high': '33.7800', '3. low': '33.5200', '4. close': '33.7500',
                                   '5. volume': '13438950'},
                    '2017-10-05': {'1. open': '33.5800', '2. high': '33.6700', '3. low': '33.4100', '4. close': '33.5900',
                                   '5. volume': '14301206'},
                    '2017-10-04': {'1. open': '33.5300', '2. high': '33.5600', '3. low': '33.2900', '4. close': '33.4400',
                                   '5. volume': '14606016'},
                    '2017-10-03': {'1. open': '33.7200', '2. high': '33.9000', '3. low': '33.6100', '4. close': '33.8500',
                                   '5. volume': '13159079'},
                    '2017-10-02': {'1. open': '33.6100', '2. high': '33.7700', '3. low': '33.5200', '4. close': '33.7500',
                                   '5. volume': '16443224'},
                    '2017-09-29': {'1. open': '33.3100', '2. high': '33.6700', '3. low': '33.2400', '4. close': '33.6300',
                                   '5. volume': '14419404'},
                    '2017-09-28': {'1. open': '33.2200', '2. high': '33.4600', '3. low': '33.2200', '4. close': '33.3500',
                                   '5. volume': '14689819'},
                    '2017-09-27': {'1. open': '33.7800', '2. high': '33.9200', '3. low': '33.3000', '4. close': '33.4800',
                                   '5. volume': '21687593'},
                    '2017-09-26': {'1. open': '33.7600', '2. high': '34.1000', '3. low': '33.6700', '4. close': '33.7600',
                                   '5. volume': '25835270'},
                    '2017-09-25': {'1. open': '33.3100', '2. high': '33.8400', '3. low': '33.2000', '4. close': '33.7200',
                                   '5. volume': '30475969'},
                    '2017-09-22': {'1. open': '32.6600', '2. high': '33.5300', '3. low': '32.6400', '4. close': '33.3700',
                                   '5. volume': '27904695'},
                    '2017-09-21': {'1. open': '32.7200', '2. high': '32.9000', '3. low': '32.5000', '4. close': '32.7000',
                                   '5. volume': '19762651'},
                    '2017-09-20': {'1. open': '32.5500', '2. high': '32.7500', '3. low': '32.3900', '4. close': '32.6000',
                                   '5. volume': '18701702'},
                    '2017-09-19': {'1. open': '32.4600', '2. high': '32.6500', '3. low': '32.4000', '4. close': '32.4900',
                                   '5. volume': '12424056'},
                    '2017-09-18': {'1. open': '32.4300', '2. high': '32.6600', '3. low': '32.2600', '4. close': '32.5200',
                                   '5. volume': '17035443'},
                    '2017-09-15': {'1. open': '32.2000', '2. high': '32.5000', '3. low': '32.1200', '4. close': '32.4400',
                                   '5. volume': '27708447'},
                    '2017-09-14': {'1. open': '31.9100', '2. high': '32.2200', '3. low': '31.9100', '4. close': '32.1900',
                                   '5. volume': '17711003'},
                    '2017-09-13': {'1. open': '32.3400', '2. high': '32.3900', '3. low': '31.9600', '4. close': '32.1800',
                                   '5. volume': '21872095'},
                    '2017-09-12': {'1. open': '32.3000', '2. high': '32.4700', '3. low': '32.1900', '4. close': '32.4100',
                                   '5. volume': '18510454'},
                    '2017-09-11': {'1. open': '31.7100', '2. high': '32.3000', '3. low': '31.6700', '4. close': '32.1900',
                                   '5. volume': '21365590'},
                    '2017-09-08': {'1. open': '31.6800', '2. high': '31.7800', '3. low': '31.4600', '4. close': '31.4800',
                                   '5. volume': '15115756'},
                    '2017-09-07': {'1. open': '31.9600', '2. high': '31.9700', '3. low': '31.7400', '4. close': '31.7600',
                                   '5. volume': '14611809'},
                    '2017-09-06': {'1. open': '31.7500', '2. high': '31.9100', '3. low': '31.6300', '4. close': '31.8700',
                                   '5. volume': '16380030'},
                    '2017-09-05': {'1. open': '32.1500', '2. high': '32.2400', '3. low': '31.4600', '4. close': '31.6200',
                                   '5. volume': '24327663'},
                    '2017-09-01': {'1. open': '32.2200', '2. high': '32.3500', '3. low': '32.0300', '4. close': '32.3000',
                                   '5. volume': '14661162'},
                    '2017-08-31': {'1. open': '32.1000', '2. high': '32.3400', '3. low': '31.9900', '4. close': '32.2100',
                                   '5. volume': '27138172'},
                    '2017-08-30': {'1. open': '31.4700', '2. high': '32.2000', '3. low': '31.4200', '4. close': '31.9900',
                                   '5. volume': '23028578'},
                    '2017-08-29': {'1. open': '31.2600', '2. high': '31.6300', '3. low': '31.1900', '4. close': '31.4800',
                                   '5. volume': '16192694'},
                    '2017-08-28': {'1. open': '31.6000', '2. high': '31.6600', '3. low': '31.4100', '4. close': '31.5400',
                                   '5. volume': '12747867'},
                    '2017-08-25': {'1. open': '31.3900', '2. high': '31.8000', '3. low': '31.3600', '4. close': '31.4400',
                                   '5. volume': '19351094'},
                    '2017-08-24': {'1. open': '30.9500', '2. high': '31.4000', '3. low': '30.9000', '4. close': '31.2400',
                                   '5. volume': '21867401'},
                    '2017-08-23': {'1. open': '31.2100', '2. high': '31.4000', '3. low': '30.9100', '4. close': '30.9200',
                                   '5. volume': '22269978'},
                    '2017-08-22': {'1. open': '30.8500', '2. high': '31.3300', '3. low': '30.7500', '4. close': '31.2700',
                                   '5. volume': '24438367'},
                    '2017-08-21': {'1. open': '30.3700', '2. high': '30.8000', '3. low': '30.3600', '4. close': '30.6800',
                                   '5. volume': '24025228'},
                    '2017-08-18': {'1. open': '31.0000', '2. high': '31.0600', '3. low': '30.3600', '4. close': '30.3700',
                                   '5. volume': '34622147'},
                    '2017-08-17': {'1. open': '31.4900', '2. high': '31.7700', '3. low': '30.8500', '4. close': '31.0400',
                                   '5. volume': '51557052'},
                    '2017-08-16': {'1. open': '32.1000', '2. high': '32.4700', '3. low': '32.0600', '4. close': '32.3400',
                                   '5. volume': '27088237'},
                    '2017-08-15': {'1. open': '31.8500', '2. high': '32.2100', '3. low': '31.8400', '4. close': '32.0900',
                                   '5. volume': '24406258'},
                    '2017-08-14': {'1. open': '31.6900', '2. high': '31.8900', '3. low': '31.5600', '4. close': '31.8400',
                                   '5. volume': '21605411'},
                    '2017-08-11': {'1. open': '31.2300', '2. high': '31.5500', '3. low': '31.0400', '4. close': '31.4700',
                                   '5. volume': '20521935'},
                    '2017-08-10': {'1. open': '31.5600', '2. high': '31.5600', '3. low': '31.0000', '4. close': '31.0000',
                                   '5. volume': '22748854'},
                    '2017-08-09': {'1. open': '31.5500', '2. high': '31.6800', '3. low': '31.3600', '4. close': '31.6200',
                                   '5. volume': '15931711'},
                    '2017-08-08': {'1. open': '31.7500', '2. high': '32.0000', '3. low': '31.6000', '4. close': '31.6700',
                                   '5. volume': '13632423'},
                    '2017-08-07': {'1. open': '31.7900', '2. high': '31.8800', '3. low': '31.6900', '4. close': '31.8400',
                                   '5. volume': '11730203'},
                    '2017-08-04': {'1. open': '31.6700', '2. high': '31.9100', '3. low': '31.5800', '4. close': '31.8000',
                                   '5. volume': '16322686'},
                    '2017-08-03': {'1. open': '31.5900', '2. high': '31.7200', '3. low': '31.4300', '4. close': '31.5600',
                                   '5. volume': '13884046'},
                    '2017-08-02': {'1. open': '31.5700', '2. high': '31.5700', '3. low': '31.2500', '4. close': '31.5200',
                                   '5. volume': '15797711'},
                    '2017-08-01': {'1. open': '31.5900', '2. high': '31.6600', '3. low': '31.4300', '4. close': '31.6500',
                                   '5. volume': '12727298'},
                    '2017-07-31': {'1. open': '31.5400', '2. high': '31.5900', '3. low': '31.3700', '4. close': '31.4500',
                                   '5. volume': '18534978'},
                    '2017-07-28': {'1. open': '31.4500', '2. high': '31.6000', '3. low': '31.2600', '4. close': '31.5200',
                                   '5. volume': '15509841'},
                    '2017-07-27': {'1. open': '31.7300', '2. high': '31.7500', '3. low': '31.2100', '4. close': '31.5700',
                                   '5. volume': '21224338'},
                    '2017-07-26': {'1. open': '32.1200', '2. high': '32.2300', '3. low': '31.5100', '4. close': '31.6600',
                                   '5. volume': '21472799'},
                    '2017-07-25': {'1. open': '31.9000', '2. high': '32.2500', '3. low': '31.8800', '4. close': '32.1200',
                                   '5. volume': '14848920'},
                    '2017-07-24': {'1. open': '31.8600', '2. high': '31.9300', '3. low': '31.6600', '4. close': '31.8600',
                                   '5. volume': '15232167'},
                    '2017-07-21': {'1. open': '31.8600', '2. high': '32.0300', '3. low': '31.7100', '4. close': '31.8400',
                                   '5. volume': '13271427'},
                    '2017-07-20': {'1. open': '31.9100', '2. high': '32.0500', '3. low': '31.7600', '4. close': '31.8600',
                                   '5. volume': '15917114'},
                    '2017-07-19': {'1. open': '31.5100', '2. high': '32.0500', '3. low': '31.4600', '4. close': '31.9000',
                                   '5. volume': '21369697'},
                    '2017-07-18': {'1. open': '31.4100', '2. high': '31.5100', '3. low': '31.1700', '4. close': '31.5100',
                                   '5. volume': '15366450'},
                    '2017-07-17': {'1. open': '31.5000', '2. high': '31.6400', '3. low': '31.4500', '4. close': '31.5000',
                                   '5. volume': '16012951'},
                    '2017-07-14': {'1. open': '31.3700', '2. high': '31.4500', '3. low': '31.2700', '4. close': '31.4200',
                                   '5. volume': '13261554'},
                    '2017-07-13': {'1. open': '31.2600', '2. high': '31.2800', '3. low': '31.0800', '4. close': '31.2700',
                                   '5. volume': '15870454'},
                    '2017-07-12': {'1. open': '31.2500', '2. high': '31.4400', '3. low': '31.1450', '4. close': '31.1600',
                                   '5. volume': '18428809'}}}

        logging.debug("Server response: %s" % json_result)

        ticker_update['metadata'] = json_result['Meta Data']
        last_refreshed = ticker_update['metadata']['3. Last Refreshed']
        if reg_datetime.match(last_refreshed):
            update_dt = datetime.strptime(last_refreshed, '%Y-%m-%d %H:%M:%S')
        else:
            update_dt = datetime.strptime(last_refreshed, '%Y-%m-%d')
        update_date = update_dt.strftime('%Y-%m-%d')

        # TODO remove commented old method of getting daily price update
        # ticker_update['last'] = json_result['Time Series (Daily)'][update_date]
        # results[ticker] = ticker_update
        ticker_update['last'] = get_stock_price(json_result['Time Series (Daily)'], update_date)
        results[ticker] = ticker_update
        logging.debug('Update: %s = %s' % (ticker, results[ticker]))

    return results


def send_notification(user_address, tickers):
        msg_body = ''
        header = None

        for ticker in tickers:
            if not header:
                msg_body += 'Update: ' + tickers[ticker]['metadata']['3. Last Refreshed'] + '\n'
                header=True
            close_price = tickers[ticker]['last']['price']
            close_change = tickers[ticker]['last']['change']
            change_pct = tickers[ticker]['last']['change_pct']
            msg_body += ('{} ${:.2f}, {:+.2f} ({:.2f}%)\n'.format(ticker,close_price,close_change,change_pct))
        logging.debug('New message: %s' % msg_body)

        if not DEBUG:
            twilio_phone, twilio_sid, twilio_auth = get_twilio_config()
            if all([twilio_phone, twilio_auth, twilio_sid]):
                t_client = Client(twilio_sid, twilio_auth)

                msg = t_client.messages.create(to=user_address, from_=twilio_phone, body=msg_body)
                logging.debug('Message SID: {}'.format(msg.sid))


def main():
    user_config = load_config()
    logging.debug('Config: %s' % user_config)

    if user_config:
        stock_update = get_stock_updates(user_config['tickers'])
        send_notification(user_config['user'], stock_update)
    else:
        pass

# Check for CLI parameter 'DEBUG'
if len(sys.argv) > 1 :
    DEBUG = True

if __name__ == "__main__":
    main()
