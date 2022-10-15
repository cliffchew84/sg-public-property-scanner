# Contents of ~/my_app/main_page.py
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
### SG Public Housing Prices - 2022

This is a proof-of-concept self-serve tool for anyone who want to search for past HDB resale transactions in Singapore since 2022. I hope this tool can help equip both Singapore property sellers and buyers with more information about their potential transactions. **Please look at my [Medium post]() for how to better use this web service.**

---

##### Some points
1. Housing transaction data is taken from ***[data.gov.sg](https://data.gov.sg/dataset/resale-flat-prices)***.
2. Home coordinates for the map visualisation are taken from the ***[Singapore OneMap API](https://www.onemap.gov.sg/docs/)***.
3. Feel free to connect with me on ***[Linkedin](https://www.linkedin.com/in/cliff-chew-kt/)*** if you have any feedback, comments or suggestions.
4. Anyone who finds value from this can buy me some coffee ***[here](https://www.buymeacoffee.com/cliffchew)***.
""")