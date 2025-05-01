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

st.write("# Analysing and predicting seasonal effects on stock pricing")

st.markdown(
    """
    This project investigates recurring seasonal patterns in stock prices—such as those around dividends, earnings, and holidays—that are often overlooked by retail trading platforms despite long-standing academic evidence. By statistically validating these effects and packaging them into a user-friendly tool, the project empowers individual investors to make more informed, timing-sensitive decisions that challenge the assumptions of market efficiency.
    
    ## Top Picks

    A summary of the most exploitable strategies based on our analysis.

    ## Dividend Strategies

    Analysis of the effects of dividend announcement and payment on stock prices. 

    ## Earnings Strategies

    Analysis of the effects of earnings announcements on stock prices. 

    ## Sell in May Strategies

    Analysis of the effects of exploiting the historical observation that stock market returns tend to be weaker in the six-month period from May to October compared to the period from November to April.

    ## Easter Strategies

    Analysis of the effects of exploiting variations in stock prices around the Easter holiday. 

    ## Christmas Strategies

    Analysis of the effects of exploiting variations in stock prices around the Christmas holiday. 

"""
    )



