# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 11:18:14 2020

@author: richlink
"""


import os
import pandas as pd
import requests


import geopy.distance
import telegram

def parse_html_response(content):
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    p_s = soup.find_all('p')
    time_update = None
    lat, long = None, None
    for p in p_s:
        t = p.text
        print(t)
        if "Position Received: " in t:
            t = t.split('UTC')[0].strip()
            time_update = pd.to_datetime(t, format="Position Received: %Y-%m-%d %H:%M")
        if "Latitude / Longitude: " in t:
            elem = t.split(' ')
            # last element is the ° sign -> has to be ommitted
            lat, long = float(elem[3][:-1]), float(elem[5][:-1])
            
    return time_update, lat, long


def get_marine_data_selenium():
    
    import time
    from selenium import webdriver
    # from selenium.webdriver.chrome.options import Options  
    
    url = "https://www.marinetraffic.com/en/ais/details/ships/shipid:5754836/mmsi:211191540/vessel:LA FLACA"                     

    # chrome_options = Options()  
    # chrome_options.add_argument("--headless")  
    # chrome_options.binary_location = '/Applications/Google Chrome   Canary.app/Contents/MacOS/Google Chrome Canary'
    
    # browser = webdriver.Chrome(options=chrome_options)
    browser = webdriver.Chrome()
    browser.get(url)
    time.sleep(5)
    src = browser.page_source
    
    browser.close() # closes the browser (not the driver)
    browser.quit() # __del__ of browser
    
    time_update, lat, long = parse_html_response(src)

    if time_update is None:
        raise Exception("mybe website format changed -> time received not where it should be")
        
    if lat is None or long is None:
        raise Exception("mybe website format changed -> lat long not where it should be")
    
    return time_update, lat, long


def parse_requests_response(result):
    """
        cleanup the json return struct by
            - creating valid timestamps from the int times (maybe not helpful?)
            - deflate the sub-dictionaries into the root element for easier pandas parsing
    """
    result['timestamp'] = pd.Timestamp(result['lastPos'], unit='s')
    del result['lastPos']
    if 'departurePort' in result and result['departurePort'] is not None:
        result['departurePort']['timestamp'] = pd.Timestamp(result['departurePort']['timestamp'], unit='s')
    
    if 'arrivalPort' in result and result['arrivalPort'] is not None:
        result['arrivalPort']['timestamp'] = pd.Timestamp(result['arrivalPort']['timestamp'], unit='s')
    
    for elem in ['departurePort', 'arrivalPort']:
        if elem in result and result[elem] is not None:
            for key, value in result[elem].items():
                result[elem + '_' + key] = value
                
            del result[elem]
    
    df = pd.DataFrame(result, index=[result['timestamp']])
    return df
        
        
        
def get_marine_data_requests():
    """
        Request URL: https://www.marinetraffic.com/vesselDetails/latestPosition/shipid:5754836
    url = "https://www.marinetraffic.com/en/vesselDetails/vesselInfo/shipid:5754836"
    
    """
    url = "https://www.marinetraffic.com/vesselDetails/latestPosition/shipid:5754836"
    
    headers = {
	    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Mobile Safari/537.36",
        "Referer": "https://www.marinetraffic.com/en/ais/details/ships/shipid:5754836/mmsi:211191540/imo:0/vessel:LA_FLACA",
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest"
        }
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        result = resp.json()
        return parse_requests_response(result)
    
    else:
        raise Exception("error [{0}]: could not read url".format(resp.status_code))



#%%
    

# tutorial
# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py


def telegram_send_message_to_scali(message):
    
    # Telegram Bot Authorization Token
    # scali_bot token: 
    with open('security_token.txt', 'r') as f:
    	token = f.read()
    	
    bot = telegram.Bot(token)
    
    # scali_logs chat group:
    scali_logs_id = -391443046
    
    bot.send_message(scali_logs_id, message)
    



#%%
"""
# calculate values

def update_interval(last, now):
    
    diff = now - last
    
"""

def get_distance(df):
    if len(df) == 1:
        return 0
    
    lat, long = df.iloc[-1]['lat'], df.iloc[-1]['lon']
    lat2, long2 = df.iloc[-2]['lat'], df.iloc[-2]['lon']
    return geopy.distance.distance((lat, long), (lat2, long2)).km


def main():

    new_data = get_marine_data_requests()

    cache_file = 'cache.csv'

    if os.path.isfile(cache_file):
        data = pd.read_csv(cache_file, index_col=0)
        data.index = pd.to_datetime(data.index.values)
    else:
        # prime the csv file
        new_data.to_csv(cache_file)
        data = new_data

    last_update = data.index[-1]

    if new_data.index[0] > last_update:
        print("got new data")
        data = pd.concat([data, new_data])
        print("saving data")
        data.to_csv(cache_file)
        
        # check if the ship has moved noticably
        distance_travelled = get_distance(data)
        # finally send a message to telegram
        telegram_msg = "new data point, travelled {0:.2f} km. {1}. current position: ".format( \
            distance_travelled,
            str(new_data.index[0])) + \
                "https://www.google.com/maps/search/?api=1&query={0},{1}".format(
                    new_data['lat'].values[0],  new_data['lon'].values[0])
                
        if  distance_travelled > 0.5:
            telegram_send_message_to_scali(telegram_msg)
        print(telegram_msg)
    else:
        print("no new data - going back to sleep")


if __name__ == '__main__':
    main()























