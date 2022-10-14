#!/usr/bin/env python
# coding: utf-8

import os
import tempfile
import requests
import pygsheets
import numpy as np
import pandas as pd
from sys import platform
from datetime import datetime
from onemap_fun import *

if platform == "darwin":
    json_encode = os.environ['g_cred'].replace("\\\\", "\\").encode('utf-8')

else:
    json_encode = st.secrets['g_cred'].replace("\\\\", "\\").encode('utf-8')

def _google_creds_as_file():
    temp = tempfile.NamedTemporaryFile()
    temp.write(json_encode)
    temp.flush()
    return temp

def execute_data_extraction():
    creds_file = _google_creds_as_file()
    gc = pygsheets.authorize(service_account_file=creds_file.name)

    ## Direct API call
    url = 'https://data.gov.sg/api/action/datastore_search?resource_id=f1765b54-a209-4718-8d38-a39237f502b3&limit=1000000&q=2022'
    response = requests.get(url).json()
    df = pd.DataFrame(response['result']['records'])

    df['year'] = pd.to_datetime(df['month']).dt.year
    df = df[df['year'] >= 2022]

    df.columns = [i.replace('_', ' ') for i in df.columns]
    df.rename(columns={
            'month':'period',
            'storey range': 'floor',
            'floor area sqm': 'sqm',
            'flat model': 'model',
            'lease commence date': 'lease date',
            'remaining lease': 'lease left',
            'resale price': 'price',
            }, inplace=True)

    # Data Cleaning
    df['floor'] = [i.replace('TO', '-') for i in df['floor']]
    df['lease year'] = [float(i.split("years")[0]) for i in df['lease left']]
    df['lease month'] = [float(i.split(" ")[-2]) / 12 if 'month' in i else 0 for i in df['lease left']]
    df['lease'] = df['lease year'] + df['lease month']

    df = df[['period', 'town', 'flat type', 'block', 'street name', 'model', 'floor', 'sqm', 'lease', 'price']]

    # Cleaning flat type
    df['flat type'] = [i.replace(' ROOM', 'R') for i in df['flat type']]
    df['flat type'] = [i.replace('EXECUTIVE', 'EC') for i in df['flat type']]
    df['flat type'] = [i.replace('-', ' ') for i in df['flat type']]
    df['flat type'] = [i.replace('MULTI GENERATION', 'MG') for i in df['flat type']]

    # Cleaning model
    df['model'] = [i.capitalize() for i in df['model']]

    # Create OneMap API callable address
    df['address'] = df['block'] + " " + df['street name']

    # Current lat long flo
    sh = gc.open('SG Public Housing Data')

    wks = sh.worksheet_by_title("Lat_Long")
    current_lat_lon = wks.get_as_df()
    current_lat_lon.lat = current_lat_lon.lat.astype(float)
    current_lat_lon.lon = current_lat_lon.lon.astype(float)

    # Combining the existing lat lon to current transactions
    current_locations = df[['address']].drop_duplicates().reset_index(drop=True)
    address_to_call = pd.merge(
        current_locations, current_lat_lon, on='address', how='left')
    address_to_call = address_to_call[address_to_call.lat.isnull()]

    # Make OneMap API call if necessary
    if address_to_call.shape[0] > 0:
        loc_main = dict()
        for add in tqdm(address_to_call['address'].tolist()):
            loc_main[add] = onemap_location_best_match(add)

        updated_lat_lon = pd.DataFrame.from_dict(loc_main).T.reset_index()
        updated_lat_lon = updated_lat_lon[['index', 'LATITUDE', 'LONGITUDE']]
        updated_lat_lon.columns = ['address', 'lat', 'lon']
        updated_lat_lon = current_lat_lon.append(updated_lat_lon).drop_duplicates().reset_index(drop=True)
        
    else:
        updated_lat_lon = current_lat_lon.copy()

    final_df = pd.merge(
        df, updated_lat_lon[['address', 'lat', 'lon']], 
        on='address', how='left')
    
    del final_df['address']
    final_df['lease'] = [round(i, 2) for i in final_df['lease']]
    final_df['lease'] = final_df['lease'].astype(str)
    final_df['price'] = final_df['price'].astype(str)

    # Find better ways to label my map tooltip
    final_df['display'] = final_df['flat type'] + " | " + final_df['model'] + " | " + final_df['lease'] + " | $" + final_df['price']

    # ### Create Year-Month columns
    final_df['year'] = [i.split('-')[0] for i in final_df.period]
    final_df['mth'] = [i.split('-')[-1] for i in final_df.period]

    date_of_update = pd.DataFrame([str(datetime.now().date())])
    date_of_update.columns = [date_of_update]

    # Push data into Google Sheet
    wks = sh.worksheet_by_title("Latest")
    wks.clear('*')
    wks.set_dataframe(final_df,(1,1))

    wks = sh.worksheet_by_title("Lat_Long")
    wks.clear('*')
    wks.set_dataframe(updated_lat_lon,(1,1))

    wks = sh.worksheet_by_title("Timing")
    wks.clear('*')
    wks.set_dataframe(date_of_update,(1,1))