import os, streamlit as st
from utils import draw_header_with_yahoo
from utils import load_symbols

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Holiday Strategies",
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

st.write("## Holiday Strategies")

draw_header_with_yahoo(symbol)
