# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 11:18:14 2020

@author: richlink
"""


import pandas as pd

from selenium import webdriver
from bs4 import BeautifulSoup

def get_marinetraffic_data():
    
    browser = webdriver.Firefox()
    browser.get("https://www.marinetraffic.com/en/ais/details/ships/shipid:5754836/mmsi:211191540/vessel:LA FLACA")
    
    src = browser.page_source
    
    browser.close() # closes the browser (not the driver)
    browser.quit() # __del__ of browser    
    
    soup = BeautifulSoup(src, 'html.parser')
    
    p_s = soup.find_all('p')
    time_update = None
    lat, long = None, None
    for p in p_s:
        t = p.text
        if "Position Received: " in t:
            t = t.split('UTC')[0].strip()
            time_update = pd.to_datetime(t, format="Position Received: %Y-%m-%d %H:%M")
        if "Latitude / Longitude: " in t:
            elem = t.split(' ')
            # last element is the ° sign -> has to be ommitted
            lat, long = float(elem[3][:-1]), float(elem[5][:-1])

    if time_update is None:
        raise Exception("mybe website format changed -> time received not where it should be")
        
    if lat is None or long is None:
        raise Exception("mybe website format changed -> lat long not where it should be")
    
    return time_update, lat, long


#%%
    

# tutorial
# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py

import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep

proxy_args = {
    'proxy_url': 'http://rb-proxy-static.bosch.com:8080',
    # Optional, if you need authentication:
    'urllib3_proxy_kwargs': {
        'username': 'richlink',
        'password': 'TheMiddle001',
    }
}

def telegram_send_message_to_scali(message):
    update_id = None
    
    # Telegram Bot Authorization Token
    # scali_bot token: 
    with open('security_token.txt', 'r') as f:
    	token = f.read()
    	
    bot = telegram.Bot(token, request_kwargs=proxy_args)
    
    # scali_logs chat group:
    scali_logs_id = -391443046
    
    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    bot.send_message(scali_logs_id, message)
    
    
telegram_send_message_to_scali("test")


#%%

# calculate values
import geopy.distance


# geopy.distance.distance((lat, long), (lat, long)).km


def update_interval(last, now):
    
    diff = now - last
    
    
    
import os

time_update, lat, long = get_marinetraffic_data()

new_data = pd.DataFrame([[lat, long]], index=[time_update], columns=["lat", "long"])

    
cache_file = 'cache.csv'

if os.path.isfile(cache_file):
    data = pd.read_csv(cache_file, index_col=0)
    data.index = pd.to_datetime(data.index.values)
else:
    # prime the csv file
    data.to_csv(cache_file)
    
last_update = data.index[-1]

if time_update > last_update:
    print("got new data")
    data = pd.concat([data, new_data])
    print("saving data")
    data.to_csv(cache_file)
    # finally send a message to telegram
    telegram_send_message_to_scali("new data point {0}: {1}° lat | {2}° long".format(
            str(time_update), lat, long))
else:
    print("no new data - going back to sleep")
    
























