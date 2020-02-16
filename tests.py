# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 11:18:14 2020

@author: richlink
"""


import pandas as pd

from selenium import webdriver
from bs4 import BeautifulSoup
import time

def get_marinetraffic_data():
    
    browser = webdriver.Chrome()
    browser.get("https://www.marinetraffic.com/en/ais/details/ships/shipid:5754836/mmsi:211191540/vessel:LA FLACA")
    time.sleep(5)
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

def telegram_send_message_to_scali(message):
    update_id = None
    
    # Telegram Bot Authorization Token
    # scali_bot token: 
    with open('security_token.txt', 'r') as f:
    	token = f.read()
    	
    bot = telegram.Bot(token)
    
    # scali_logs chat group:
    scali_logs_id = -391443046
    
    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    bot.send_message(scali_logs_id, message)
    
    
# telegram_send_message_to_scali("test")


#%%
"""
# calculate values
import geopy.distance

dist =[]

for a, b in zip(data.iloc[:-1].values, data.iloc[1:].values):
    lat, long = a
    lat2, long2 = b
    dist.append(geopy.distance.distance((lat, long), (lat2, long2)).km)
    
                
def update_interval(last, now):
    
    diff = now - last
    
"""
    
import os

time_update, lat, long = get_marinetraffic_data()

new_data = pd.DataFrame([[lat, long]], index=[time_update], columns=["lat", "long"])

    
cache_file = 'cache.csv'

if os.path.isfile(cache_file):
    data = pd.read_csv(cache_file, index_col=0)
    data.index = pd.to_datetime(data.index.values)
else:
    # prime the csv file
    new_data.to_csv(cache_file)
    data = new_data
    
last_update = data.index[-1]

if time_update > last_update:
    print("got new data")
    data = pd.concat([data, new_data])
    print("saving data")
    data.to_csv(cache_file)
    # finally send a message to telegram
    telegram_msg = "new data point from {0}. current position: ".format(str(time_update)) + \
            "https://www.google.com/maps/search/?api=1&query={0},{1}".format(
                lat, long)
    telegram_send_message_to_scali(telegram_msg)
else:
    print("no new data - going back to sleep")
    

























