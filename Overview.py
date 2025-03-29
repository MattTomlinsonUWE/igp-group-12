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

# Path to the CSV file
csv_path = "./data/overview.csv"

# Check if file exists
if os.path.exists(csv_path):
    # Load the CSV file
    df = pd.read_csv(csv_path)
    

    # Display data
    st.subheader("Sample Results")
    st.markdown(
        df.to_html(index=False, escape=False),
        unsafe_allow_html=True
    )

else:
    st.error(f"File '{csv_path}' not found. Please make sure it exists in the app directory.")


