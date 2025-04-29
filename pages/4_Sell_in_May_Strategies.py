import os, streamlit as st
import pandas as pd
from utils import draw_header_with_yahoo
from utils import load_symbols

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Sell in May Strategies",
    page_icon="chart_with_upwards_trend",
    layout="wide",
)

# Default symbol
symbol = "AAPL"

# Set-up symbol picker 
symbols = load_symbols()

# Retrieve symbol from session state
try: 
    symbol = st.session_state['ticker']
except Exception as e:
     symbol = "AAPL"

# Retrieve symbol from query params
params = st.query_params.get_all

# Extract unique stock tickers for autocomplete
tickers = symbols["Symbol"].unique().tolist()

tickers_idx = tickers.index(symbol)

# Draw the tickers list and the disclaimer on the sidebar
with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")
    
if params("symbol"):
    symbol = params("symbol")[0].upper()

st.write("# Stock Market Seasonality Strategies")

st.write("## 'Sell in May' Strategies")

draw_header_with_yahoo(symbol)

# import output_sell_in_may.csv
csv_path = "./data/output_sell_in_may.csv"

# Check if file exists
if os.path.exists(csv_path):
    # Load the CSV file
    df = pd.read_csv(csv_path)

    # check if our symbol is within it
    result = df[df.iloc[:, 0].str.contains(symbol, case=False, na=False)]

    if result.empty:
        st.write("No data found for this stock.")
    else:
        st.write("### Overview")
        st.write("The figures below provide a detailed look at the seasonal performance of the stock over a 15 year period comprising comprise various performance metrics split between the two significant investment periods: November to April and May to October. ")

        st.write("### Nov to Apr Better (%):")
        st.write("The percentage of years where the stock’s returns were higher in the November-April period compared to the May-October period.")
        st.write(result["NovApr Better (%)"].values[0])

        st.write("### Nov to Apr Avg Rtn (15Y):")
        st.write("The average return from November to April over 15 years, presented as a percentage. This highlights the typical performance investors might expect during this period.")
        st.write(result["NovApr Avg Rtn (15Y)"].values[0])

        st.write("### May to Oct Avg Rtn (15Y):")
        st.write("The average return from May to October over 15 years, also as a percentage. This serves as a comparative measure against the Nov-Apr returns.")
        st.write(result["MayOct Avg Rtn (15Y)"].values[0])

        st.write("### Nov to Apr Cum Rtn (15Y):")
        st.write("The total cumulative return achieved by the stock during the November to April periods across 15 years.")
        st.write(result["NovApr Cum Rtn (15Y)"].values[0])

        st.write("### May to Oct Cum Rtn (15Y):")
        st.write("The total cumulative return during the May to October periods across 15 years.")
        st.write(result["MayOct Cum Rtn (15Y)"].values[0])
        
        st.write("### Nov to Apr Vol (15Y):")
        st.write("The volatility (standard deviation of returns) for each period, providing insight into the risk or variability in returns during these times.")
        st.write(result["NovApr Vol (15Y)"].values[0])
        
        st.write("### May to Oct Vol (15Y):")
        st.write("The volatility (standard deviation of returns) for each period, providing insight into the risk or variability in returns during these times.")
        st.write(result["MayOct Vol (15Y)"].values[0])
