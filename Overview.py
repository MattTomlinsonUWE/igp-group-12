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

st.write("# Stock Market Seasonality Strategies")

st.markdown(
    """
    Here are some of the seasonality strategies we have created
    
    """
    )

st.markdown("""
    <style>
        th {
            text-align: left !important;
        }
    </style>
""", unsafe_allow_html=True)

# Path to the CSV file
csv_path = "./data/overview.csv"

# Check if file exists
if os.path.exists(csv_path):
    # Load the CSV file
    df = pd.read_csv(csv_path)
    
    # We do a little cleanup on the table
    df.replace("Null", " ", inplace=True)

    # Display data
    #st.subheader("Sample Results")
    #st.markdown(
    #    df.to_html(index=False, escape=False),
    #    unsafe_allow_html=True
    #)

    # Draw header row
    header_cols = st.columns(len(df.columns))
    for col, col_name in zip(header_cols, df.columns):
        col.markdown(f"**{col_name}**")  # Bold headers

    # Build table manually
    for i, row in df.iterrows():
        cols = st.columns(len(row))
        for j, (col_name, cell_value) in enumerate(row.items()):
            if col_name == "Ticker" or col_name == "Stock" or cell_value == " ":
                cols[j].write(f"**{cell_value}**")  # Just display ticker
            else:
                # Create a unique key for each button
                key = f"{row['Ticker']}_{col_name}_{i}"
                if cols[j].button(cell_value, key=key):
                    st.success(f"Clicked: {row['Ticker']} - '{col_name}' = {cell_value}")
                    # You can trigger any custom action here
                    if col_name == "Sell in May":
                        st.session_state['ticker'] = row['Ticker']
                        st.switch_page("pages/4_Sell in May Strategies.py")

else:
    st.error(f"File '{csv_path}' not found. Please make sure it exists in the app directory.")


