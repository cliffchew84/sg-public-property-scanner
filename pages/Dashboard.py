#!/usr/bin/env python
# coding: utf-8

import os
import folium
import tempfile
import pygsheets
import numpy as np
import pandas as pd
import streamlit as st
from sys import platform
import plotly.graph_objects as go
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# Authenticate into Google Sheets
if platform == "darwin":
    json_encode = os.environ['g_cred'].replace("\\\\", "\\").encode('utf-8')

else:
    json_encode = st.secrets['g_cred'].replace("\\\\", "\\").encode('utf-8')

def _google_creds_as_file():
    temp = tempfile.NamedTemporaryFile()
    temp.write(json_encode)
    temp.flush()
    return temp

@st.cache
def pull_data():

    creds_file = _google_creds_as_file()
    gc = pygsheets.authorize(service_account_file=creds_file.name)

    sh = gc.open('SG Public Housing Data')

    wks = sh.worksheet_by_title("Latest")
    data = wks.get_as_df()
    
    ## Data Cleaning
    data['block'] = data['block'].astype(str)
    data['sqm'] = data['sqm'].astype(int)
    data['price'] = data['price'].astype(int)
    data['lease'] = data['lease'].astype(int)

    wks = sh.worksheet_by_title("Timing")
    timing = wks.get_as_df()

    return timing, data.reset_index(drop=True)

timing, data = pull_data()

# Start of UI
timing = timing[0][0]

st.markdown("### SG Public Housing Prices since 2022")
st.markdown("""
- Last updated on ***{}***.
- Remember to clear cache and reload the page to get the latest data. 
- Best viewed on desktop
---
""".format(timing))

lease_min = int(data.lease.min())
sqm_min = int(data.sqm.min())
sqm_max = int(data.sqm.max())
p_min = int(data.price.min())
p_max = int(data.price.max())

try:
    with st.sidebar:
        town_select = st.selectbox(
            'Select a town',
            tuple(data.town.drop_duplicates().tolist()))

        df = data[data['town'] == town_select].reset_index(drop=True)
        models_select = st.multiselect(
            'Select a model', 
            default='All',
            options=tuple(df.model.drop_duplicates().tolist()  + ['All',] ))

        search = st.text_input("Street Name - Not Case Sensitive", '')
        mth_start, mth_end = st.slider('Transaction Month', 1, 12, (1, 12))
        min_size, max_size = st.slider('Flat Size (sqm)', sqm_min, sqm_max, (sqm_min, sqm_max))
        
        min_lease = st.slider("Min Lease (yrs)", lease_min, 99, lease_min)
        min_price = st.number_input('Min Price ($)', p_min, p_max, p_min, 1000)
        max_price = st.number_input('Max Price ($)', p_min, p_max, p_max, 1000)

    # Applying filters
    if search:
        df = df[df['street name'].str.contains(search.upper())]

    if models_select == ["All"]:
        pass
    else:
        df = df[df['model'].isin(models_select)].reset_index(drop=True)

    df = df[(df['sqm'] >= min_size) & (df['sqm'] <= max_size)]
    df = df[(df['price'] >= min_price) & (df['price'] <= max_price)]
    df = df[df['lease'] >= min_lease]

    months_range = [i for i in range(mth_start, mth_end)]
    df = df[df['mth'].isin(months_range)]

    col1, col2 = st.columns([1,1])

    col1.markdown("##### Average for {} town".format(town_select))
    summary = df.pivot_table(
        index='model',
        values=['price', 'sqm', 'lease'], 
        aggfunc=np.mean, margins=True).reset_index()

    summary_count = df.pivot_table(
        index='model',
        values='price', 
        aggfunc='count', margins=True).reset_index()

    summary_count.columns = ['model', 'total']
    summary = summary_count.merge(summary, how='right')
    summary = summary.sort_values('total')

    summary.columns = ['model', 'total', 'lease', 'price', 'sqm']
    col1.write(summary.style.format(
        {'price': "${:,.2f}", 
        'sqm': '{:,.2f}',
        'lease': '{:,.1f}'
        })
    )

    col2.write("##### Distribution")
    fig = go.Figure()
    for model in df.model.drop_duplicates():
        fig.add_trace(go.Box(y=df[df['model']==model].price, name=model))

    fig.update_layout(
        legend=dict(orientation="h"),
        width=500, height=350,
        margin=dict(l=5, r=5, b=10, t=10, pad=0),
        showlegend=True,
        xaxis_visible=False,
    )

    col2.plotly_chart(fig)

    st.markdown("##### Transactions")
    st.write(
        df[['period', 'town', 'flat type', 'block', 'street name', 'model', 'floor', 'sqm', 'lease', 'price']], 
    unsafe_allow_html=True
    )

    map_view = st.checkbox('Show Map')
    st.write("**The map can be unstable when too many transactionsa loaded.** Please filter the necessary transactions before showing them on a map.")
    if map_view:
        try:
            df = df.reset_index(drop=True)
            m = folium.Map(location=[df['lat'][0], df['lon'][0]], zoom_start=14)
            for i in range(0, len(df['period'].tolist())):
                folium.Marker(
                    [df['lat'][i], df['lon'][i]],
                    tooltip=df['display'][i]
                    ).add_to(m)            

            st_data = st_folium(m, height=500, width=500)
        except:
            st.write("**If you see this, Please toggle on and off the 'Show Map' button**")

except:
    st.write("No data found")