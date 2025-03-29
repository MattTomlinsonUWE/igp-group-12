import os, streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
from polygon import RESTClient
from utils import draw_header_with_yahoo
from utils import load_symbols


# Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Dividend Strategies",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Read query parameters
symbol = "AAPL"

params = st.query_params.get_all

if params("symbol"):
    symbol = params("symbol")[0].upper()

# Set-up symbol picker 
symbols = load_symbols()

# Extract unique stock tickers for autocomplete
tickers = symbols["Symbol"].unique().tolist()

with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers)


    
st.write("# Stock Market Seasonality Strategies")

st.write("## Dividend Strategies")

draw_header_with_yahoo(symbol)


