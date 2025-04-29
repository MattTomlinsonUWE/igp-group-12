import os, streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
from polygon import RESTClient
from utils import draw_header_with_yahoo
from utils import load_symbols
import yfinance as yf
from scipy import stats
from PIL import Image


# Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Earnings Strategies",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Set-up symbol picker 
symbols = load_symbols()

# Retrieve symbol from session state
try: 
    symbol = st.session_state['ticker']
except Exception as e:
     symbol = "AAPL"

# Retrieve symbol from query params
params = st.query_params.get_all

if params("symbol"):
    symbol = params("symbol")[0].upper()
    
# Extract unique stock tickers for autocomplete
tickers = symbols["Symbol"].unique().tolist()

tickers_idx = tickers.index(symbol)

# Draw the tickers list on the sidebar
with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")

# Write the titles    
st.write("# Stock Market Seasonality Strategies")
st.write("## Earnings Strategies")

draw_header_with_yahoo(symbol)

st.write("## Strategy overview")
st.write("Buy the stock shortly before an earnings announcement and sell afterwards to capture the uplift in stock price around the announcement.")
st.write("## Does the strategy work for this stock?")

# We start by assuming that we don't have data for the stock
record_found = False

# Path to the CSV file
csv_path_ar = "./data/earnings_strategy_results_ar.csv"
csv_path_cr = "./data/earnings_strategy_results_cr.csv"

# Load the CSV file
if os.path.exists(csv_path_ar):
    # Load the CSV file
    df_ar = pd.read_csv(csv_path_ar)
    row_ar = df_ar.loc[df_ar['Ticker'] == symbol]

if not row_ar.empty:
    record_found = True
    
if not record_found:
    st.write("We have no data for this stock or it does not appear to work.")
else:
    st.write("This strategy appears to work based on an analysis of the period 2014 to 2022.")
    st.write("Average return (one-off): ")
    st.write("Cumulative return (whole period): ")
    st.write("## Recommended Action: One-off")
    st.write("Buy x days before announcement")
    st.write("Sell x days after announcement")
    st.write("## Recommended Action: Cumulative")
    st.write("Buy x days before announcement")
    st.write("Sell x days after announcement")
    st.write("## Recent events:")
    image = Image.open("./pictures/ali-aapl-1.jpg")
    st.image(image, caption='Effects of earnings on closing price')
    st.write("## Returns per Earnings Event:")
    image = Image.open("./pictures/ali-aapl-2.jpg")
    st.image(image, caption='Returns around each earnings event')
    st.write("## Cumulative Portfolio Growth:")
    image = Image.open("./pictures/ali-aapl-3.jpg")
    st.image(image, caption='')
    st.write("## Average Abnormal Return (AAR):")
    image = Image.open("./pictures/ali-aapl-4.jpg")
    st.image(image, caption='')
    st.write("## Cumulative Abnormal Return (CAR):")
    image = Image.open("./pictures/ali-aapl-5.jpg")
    st.image(image, caption='')


