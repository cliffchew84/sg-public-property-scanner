# Contents of ~/my_app/main_page.py
import os
import tempfile
import pygsheets
import pandas as pd
import streamlit as st
from sys import platform
from datetime import datetime
from backend_processing import execute_data_extraction

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

    wks = sh.worksheet_by_title("Timing")
    timing = wks.get_as_df()

    return timing

# Start of UI
timing = pull_data()[0][0]

st.markdown("""
### SG Public Housing Prices - 2022

This is a proof-of-concept self-serve tool for anyone who want to search for past HDB resale transactions in Singapore since 2022. I hope this tool can help equip both Singapore property sellers and buyers with more information about their potential transactions.
""")

col1, col2 = st.columns([1,1])

if col1.button("Update the data"):
    # Trigger update script
    execute_data_extraction()
    timing = str(datetime.now().date())
    col2.write("Data updated as of {}".format(timing))

else:
    col2.write("Data updated as of {}".format(timing))

st.markdown("""
##### Some other points
1. Housing transaction data is provided by and publicly available on ***[data.gov.sg](https://data.gov.sg/dataset/resale-flat-prices)***.
2. Home coordinates were taken from the ***[Singapore OneMap API](https://www.onemap.gov.sg/docs/)***, and is needed for the map visualisation. There may be some missing transactions if the home transaction addresses from ***data.gov.sg*** didn't return a corresponding coordinate.
3. Feel free to connect with me on ***[Linkedin](https://www.linkedin.com/in/cliff-chew-kt/)*** if you have any feedback, comments or suggestions.
4. Anyone who finds value from this can buy me some coffee ***[here](https://www.buymeacoffee.com/cliffchew)***.
""")