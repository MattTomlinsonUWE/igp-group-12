import os, streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
from polygon import RESTClient
import os
from utils import load_symbols

# Step 1 - Retrieve environmental variables
load_dotenv()

#TO DO - move this to the environment
POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Display the disclaimer
with st.sidebar:
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")

st.write("# Stock pricing seasonality exploration")

st.markdown(
    """
    Most non-professional stock market investors fail to realise the impact that seasonal trends have on the price of the shares that they buy and sell. 

    The price of a share can often be significantly above-trend during periods such as before an earning announcement, or depressed in a run up to a dividend payment. 

    This can also happen at certain periods of the year, such as around Christmas and Easter holidays. 

    For some shares this can be predicted with reasonable certainty, leading to not only to be able to buy and sell at the most advantageous time, but also to potentially employ short-term trading strategies.   

    For each of the most common strategies we've outlined the main effects, and also compiled our top picks. 
    
    Click the left hand menu to learn more.  

    """
    )



