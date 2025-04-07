import os, streamlit as st
from utils import draw_header_with_yahoo
from utils import load_symbols

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Holiday Strategies",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Default symbol
symbol = "AAPL"

# Set-up symbol picker 
symbols = load_symbols()

# Retrieve symbol from session state
if st.session_state['ticker'] is not None: 
    symbol = st.session_state['ticker']

# Retrieve symbol from query params
params = st.query_params.get_all

# Extract unique stock tickers for autocomplete
tickers = symbols["Symbol"].unique().tolist()

tickers_idx = tickers.index(symbol)

with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    
if params("symbol"):
    symbol = params("symbol")[0].upper()

st.write("# Stock Market Seasonality Strategies")

st.write("## Holiday Strategies")

draw_header_with_yahoo(symbol)