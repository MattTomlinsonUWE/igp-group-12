import os, streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
from polygon import RESTClient
import requests
from utils import draw_header_with_yahoo
from utils import load_symbols
import yfinance as yf
from scipy import stats
from PIL import Image
import pytz  # For timezone handling
import altair as alt #interactive charts
import numpy as np


#TO DO - move this to the environment
POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

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

# Write the titles    
st.write("# Stock Market Seasonality Strategies")
st.write("## Earnings Strategies")

# 1. Load Core Data
events = pd.read_csv("./data/earnings_strategy_events.csv", parse_dates=["Ann Date"])
meta   = pd.read_csv("./data/earnings_strategy_meta.csv",   parse_dates=["Ann Date"])
ar     = pd.read_csv("./data/earnings_strategy_ar.csv",     index_col=0)

# Clean Surprise column
meta["Surprise"] = pd.to_numeric(meta["Surprise"], errors="coerce")
meta["Surprise"] = meta["Surprise"].replace([np.inf, -np.inf], np.nan)

# 2. Build event_id & reindex meta
events["event_id"] = events["Ticker"] + " | " + events["Ann Date"].dt.date.astype(str)
meta["event_id"]   = meta["Ticker"]   + " | " + meta["Ann Date"].dt.date.astype(str)
meta = meta.set_index("event_id")

# 3. Prepare CAR windows
car0  = ar["0"]
car1  = ar[["-1","0","1"]].sum(axis=1)
car11 = ar.loc[:, [str(i) for i in range(-5,6)]].sum(axis=1)
windows = {
    "CAR(0,0)"   : car0,
    "CAR(-1,+1)" : car1,
    "CAR(-5,+5)" : car11
}

found = True

# Handle if the choice is not available
try:
    tickers_idx = sorted(events["Ticker"].unique()).index(symbol)
except Exception as e:
    found = False
    ticker = symbol 

# Draw the tickers list on the sidebar
with st.sidebar:
    if found:
        ticker = st.selectbox("Choose a ticker", sorted(events["Ticker"].unique()),tickers_idx)
        window = st.selectbox("Choose CAR window", list(windows.keys()))
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in the event that you do, no liability will be accepted for any losses.")


draw_header_with_yahoo(ticker)

st.write("### Strategy overview")
with st.container(key='colored-background-2'):
    st.write("This strategy takes advantage of predictable increases in stock price around the date of earnings announcements. ")

if found == False:
    st.error("No data for this stock.")
    st.stop()

# Determine CAR series for selected window
car_series = windows[window]

# 4.2 Filter Data for Selected Ticker
car_series = windows[window]
ev     = events[events["Ticker"] == ticker].sort_values("Ann Date")
ar_sub = ar.loc[ev["event_id"].values]
md     = meta.loc[ev["event_id"].values]

# 4.3 Key Metrics 
st.subheader("Key Metrics")
with st.container(key='colored-background-3'):
    st.markdown("_Average & most recent abnormal returns around earnings._")
    st.markdown("Use these metrics to see typical earnings impact and how the latest event compares.")

    car_win       = car_series.loc[ev["event_id"]]
    avg_car       = car_win.mean()
    last_eid      = ev.iloc[-1]["event_id"]
    last_surprise = md.loc[last_eid, "Surprise"]
    last_car      = car_win.loc[last_eid]
    n_events      = len(ev)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Avg {window}",  f"{avg_car:.2%}")
    k2.metric("Last Surprise",  f"{last_surprise:.1%}")
    k3.metric(f"Last {window}", f"{last_car:.2%}")
    k4.metric("# of Events",    f"{n_events}")

# 5. Ranking Section 
st.subheader(f"Ranking: Average {window} by Ticker")
with st.container(key='colored-background-4'):
    st.markdown("Compare tickers by their average CAR to identify top and bottom performers.")
    df_rank = (
        pd.DataFrame({"event_id": car_series.index, "CAR": car_series.values})
          .merge(events[["event_id","Ticker"]], on="event_id")
        .groupby("Ticker", as_index=False)["CAR"].mean()
        .sort_values("CAR", ascending=False)
    )
    st.dataframe(
        df_rank.rename(columns={"CAR": f"Avg {window}"})
           .style.format({f"Avg {window}": "{:.1%}"})
    )

# 6. Earnings History Table
st.subheader("Earnings History")
with st.container(key='colored-background-5'):
    st.markdown("Review each past announcement’s date, surprise, and CAR in one table.")

    df_table = ev[["event_id","Ann Date"]].copy()
    df_table["Surprise"]   = df_table["event_id"].map(md["Surprise"])
    df_table["CAR(0,0)"]   = ar_sub["0"].values
    df_table["CAR(-1,+1)"] = car_series.loc[ev["event_id"]].values
    df_table["CAR(-5,+5)"] = ar_sub.loc[:, [str(i) for i in range(-5,6)]].sum(axis=1).values
    st.dataframe(
        df_table
        .sort_values("Ann Date", ascending=False)
        .rename(columns={"Ann Date":"Date"})
        .style.format({
         "Surprise"   : "{:.1%}",
         "CAR(0,0)"   : "{:.1%}",
         "CAR(-1,+1)" : "{:.1%}",
         "CAR(-5,+5)" : "{:.1%}"
        }),
    height=300
    )


# 7. Latest AR Curve (window-sensitive)
st.subheader("Latest AR Curve")
with st.container(key='colored-background-6'):
    st.markdown("Visualize the abnormal return trajectory around the most recent earnings date.")
    #Pick only the days in your chosen window.
    full_ar = ar_sub.loc[last_eid].astype(float)
    if window == "CAR(0,0)":
        days = ["0"]
    elif window == "CAR(-1,+1)":
        days = ["-1","0","1"]
    else:
        days = [str(i) for i in range(-5,6)]
    df_curve = (
        full_ar.loc[days]
           .rename_axis("Day")
           .reset_index(name="AR")
           .assign(Day=lambda d: d.Day.astype(int))
           .set_index("Day")
    )
    st.line_chart(df_curve)

# 8. Surprise vs. CAR Scatter
st.subheader("Surprise vs. Return")
with st.container(key='colored-background-7'):
    st.markdown("Inspect how EPS surprise correlates with the selected CAR window.")
    df_sc = pd.DataFrame({
        "Surprise": md["Surprise"].values,
        "CAR"     : car_win.values,
        "Date"    : ev["Ann Date"].dt.date.values
    })
    scatter = alt.Chart(df_sc).mark_circle(size=60).encode(
        x=alt.X("Surprise", title="EPS Surprise"),
        y=alt.Y("CAR",      title=window),
        tooltip=["Date","Surprise","CAR"]
    ).interactive()
    st.altair_chart(scatter, use_container_width=True)

# 9. Build & fit cross-sectional model for selected window
st.subheader("Forecast Next Event CAR")
with st.container(key='colored-background-8'):
    st.markdown("Select a future event to view its predicted CAR and 95% confidence interval.")
    # Load only the predictions CSV and build event_id
    upcoming = pd.read_csv("./data/earnings_strategy_upcoming_predictions.csv", parse_dates=["Ann Date"])
    upcoming["event_id"] = upcoming["Ticker"] + " | " + upcoming["Ann Date"].dt.date.astype(str)

    # User selects which future event to display
    choice = st.selectbox("Pick an upcoming event", upcoming["event_id"])
    sel    = upcoming.set_index("event_id").loc[choice]

    pred_car = sel["Pred_CAR_1"]
    ci_lo    = sel["CI_lower"]
    ci_hi    = sel["CI_upper"]

    # Show the precomputed values
    st.metric(
        label = f"Predicted {window} for {choice}",
        value = f"{pred_car:.2%}",
        delta = None
    )
    st.write(f"95% CI: [{ci_lo:.2%}, {ci_hi:.2%}]")