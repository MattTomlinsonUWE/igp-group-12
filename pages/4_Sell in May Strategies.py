import os, streamlit as st
from dotenv import load_dotenv
from utils import draw_header


# Step 1 - Retrieve environmental variables
load_dotenv()

# Read query parameters
symbol = "AAPL"

params = st.query_params.get_all

if params("symbol"):
    symbol = params("symbol")[0].upper()

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Sell in May Strategies",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

st.write("# Stock Market Seasonality Strategies")

st.write("## 'Sell in May' Strategies")

draw_header(symbol)