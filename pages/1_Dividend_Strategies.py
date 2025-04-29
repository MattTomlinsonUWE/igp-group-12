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


# Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Dividend Strategies",
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

# Draw the tickers list and the disclaimer on the sidebar
with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")

# Write the titles    
st.write("# Stock Market Seasonality Strategies")
st.write("## Dividend Strategies")

draw_header_with_yahoo(symbol)

POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

client = RESTClient("Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8")

details = client.get_ticker_details(symbol)    

# Use Yahoo Finance and Polygon to determine if we have extra trading volume 
def analyze_volume_spike(ticker_symbol, period="5y", window=20, days_before=3, days_after=3):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        dividends = ticker.dividends

        if dividends.empty or hist.empty:
            return None  # No dividends or no trading data

        hist['AvgVolume'] = hist['Volume'].rolling(window=window).mean()
        hist['VolumeSpike'] = hist['Volume'] / hist['AvgVolume']

        #Use Poligon dividend data because we don't have the pay date in Yahoo Finance
        pdividends = client.list_dividends(ticker=symbol, limit=100)
        
        dividend_windows = [
            (
                pd.to_datetime(d.ex_dividend_date).tz_localize(None) - pd.Timedelta(days=days_before),
                pd.to_datetime(d.pay_date).tz_localize(None) + pd.Timedelta(days=days_after) 
            )
            for d in pdividends
                if d.ex_dividend_date and d.pay_date  # ensure both dates are present
        ]

        hist.index = hist.index.tz_localize(None)

        hist['IsDividendWeek'] = hist.index.to_series().apply(
            lambda x: any([(start <= x <= end) for (start, end) in dividend_windows])
        )
        
        dividend_periods = hist[hist['IsDividendWeek']]
        normal_periods = hist[~hist['IsDividendWeek']]

        
        avg_div_spike = dividend_periods['VolumeSpike'].mean()
        avg_non_div_spike = normal_periods['VolumeSpike'].mean()

        return {
            "Ticker": ticker_symbol,
            "AvgVolumeSpikeDiv": round(avg_div_spike, 2),
            "AvgVolumeSpikeNonDiv": round(avg_non_div_spike, 2)
        }

    except Exception as e:
        return {"Ticker": ticker_symbol, "Error": str(e)}

long_term_volume = analyze_volume_spike(symbol)

st.write("### Long-Term Dividend Strategies")
st.write("#### Is trading volume greater in dividend period?")
if long_term_volume is not None:
    if long_term_volume["AvgVolumeSpikeNonDiv"] >= long_term_volume["AvgVolumeSpikeDiv"]:
        st.write(f"No, trading volume is less during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Therefore **no extra caution** is required when trading.")
    else:
        st.write(f"Yes, trading volume is more during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Therefore **extra caution** is required when trading.")

    st.write(f" - Average Volume Spike in Dividend Period: {long_term_volume["AvgVolumeSpikeDiv"]}")
    st.write(f" - Average Volume Spike in Non-Dividend Period: {long_term_volume["AvgVolumeSpikeNonDiv"]}")
else:
    st.write("No dividends in period.")

st.write("#### Is price volatility greater in dividend period?")

# Use Yahoo Finance and Polygon to determine if we have extra trading volume 
def analyze_price_volatility(ticker_symbol, period="5y", window=20, days_before=3, days_after=3):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        dividends = ticker.dividends

        if dividends.empty or hist.empty:
            return None  # No dividends or no trading data

        hist['AvgVolume'] = hist['Volume'].rolling(window=window).mean()
        hist['VolumeSpike'] = hist['Volume'] / hist['AvgVolume']

        # Calculate absolute daily return as a measure of price movement
        hist['Return'] = hist['Close'].pct_change()
        hist['AbsReturn'] = hist['Return'].abs()

        # Rolling average of absolute returns to estimate normal volatility
        hist['AvgAbsReturn'] = hist['AbsReturn'].rolling(window=window).mean()

        # Define price spike as a ratio of actual move to average
        hist['PriceSpike'] = hist['AbsReturn'] / hist['AvgAbsReturn']

        #Use Poligon dividend data because we don't have the pay date in Yahoo Finance
        pdividends = client.list_dividends(ticker=symbol, limit=100)
        
        dividend_windows = [
            (
                pd.to_datetime(d.ex_dividend_date).tz_localize(None) - pd.Timedelta(days=days_before),
                pd.to_datetime(d.pay_date).tz_localize(None) + pd.Timedelta(days=days_after) 
            )
            for d in pdividends
                if d.ex_dividend_date and d.pay_date  # ensure both dates are present
        ]

        hist.index = hist.index.tz_localize(None)

        hist['IsDividendWeek'] = hist.index.to_series().apply(
            lambda x: any([(start <= x <= end) for (start, end) in dividend_windows])
        )

        dividend_periods = hist[hist['IsDividendWeek']]
        normal_periods = hist[~hist['IsDividendWeek']]

        
        avg_div_spike = dividend_periods['PriceSpike'].mean()
        avg_non_div_spike = normal_periods['PriceSpike'].mean()

        return {
            "Ticker": ticker_symbol,
            "AvgVolumeSpikeDiv": round(avg_div_spike, 2),
            "AvgVolumeSpikeNonDiv": round(avg_non_div_spike, 2)
        }

    except Exception as e:
        return {"Ticker": ticker_symbol, "Error": str(e)}

long_term_price = analyze_price_volatility(symbol)

if long_term_price is not None:
    if long_term_price["AvgVolumeSpikeNonDiv"] >= long_term_price["AvgVolumeSpikeDiv"]:
        st.write(f"No, price volatility is less during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Therefore **no extra caution** is required when trading.")
    else:
        st.write(f"Yes, price volatility is more during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Therefore **extra caution** is required when trading.")

    st.write(f" - Average Price Spike in Dividend Period: {long_term_price["AvgVolumeSpikeDiv"]}")
    st.write(f" - Average Price Spike in Non-Dividend Period: {long_term_price["AvgVolumeSpikeNonDiv"]}")
else:
    st.write("No dividends in period.")

st.write("#### Is the stock historically under/overpriced during period")
# Use Yahoo Finance and Polygon to determine if the stock price varies  
def analyze_dividend_price_behavior(ticker_symbol, period="5y", window=20, days_before=3, days_after=3):
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        dividends = ticker.dividends

        if dividends.empty or hist.empty:
            return None  # No dividends or no trading data

        # Calculate price return
        hist['Return'] = hist['Close'].pct_change()

        # Include dividend to compute total return
        hist['Dividend'] = hist.index.map(lambda x: dividends[x] if x in dividends.index else 0)
        hist['TotalReturn'] = hist['Return'] + (hist['Dividend'] / hist['Close'].shift(1))

        #Use Poligon dividend data because we don't have the pay date in Yahoo Finance
        pdividends = client.list_dividends(ticker=symbol, limit=100)
        
        dividend_windows = [
            (
                pd.to_datetime(d.ex_dividend_date).tz_localize(None) - pd.Timedelta(days=days_before),
                pd.to_datetime(d.pay_date).tz_localize(None) + pd.Timedelta(days=days_after) 
            )
            for d in pdividends
                if d.ex_dividend_date and d.pay_date  # ensure both dates are present
        ]

        hist.index = hist.index.tz_localize(None)

        hist['IsDividendWeek'] = hist.index.to_series().apply(
            lambda x: any([(start <= x <= end) for (start, end) in dividend_windows])
        )

        # We could change this to return
        close_div = hist[hist['IsDividendWeek']]['Close'].dropna()
        close_non_div = hist[~hist['IsDividendWeek']]['Close'].dropna()

        if len(close_div) < 5 or len(close_non_div) < 20:
            return {
                "Ticker": ticker_symbol,
                "Avg Return (Div)": None,
                "Avg Return (Non-Div)": None,
                "Return Diff (%)": None,
                "P-Value": None
            }

        # Calculate average returns
        avg_return_div = close_div.mean()
        avg_return_non_div = close_non_div.mean()
        return_diff = avg_return_div - avg_return_non_div

        # Statistical test
        t_stat, p_val = stats.ttest_ind(close_div, close_non_div, equal_var=False)

        return {
            "Ticker": ticker_symbol,
            "AvgPriceDiv": round(avg_return_div, 4),
            "AvgPriceNonDiv": round(avg_return_non_div, 4),
            "PriceDiff": round(return_diff * 100, 2),
            "PValue": round(p_val, 4)
        }

    except Exception as e:
        return {"Ticker": ticker_symbol, "Error": str(e)}

long_term_return = analyze_dividend_price_behavior(symbol)

if long_term_return is not None:
    if long_term_return["AvgPriceNonDiv"] >= long_term_return["AvgPriceDiv"]:
        st.write(f"The average price is less during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Consider buying during this time.")
    else:
        st.write(f"The average price is more during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
        st.write("Consider waiting until this time is over.")
        st.write("TO DO - evaluate the merit of this strategy.")

    st.write(f" - Average Price in Dividend Period (excluding dividend): {long_term_return["AvgPriceDiv"]}")
    st.write(f" - Average Price in Non-Dividend Period: {long_term_return["AvgPriceNonDiv"]}")
else: 
    st.write("No dividends in period.")

st.write("### Short-Term Dividend Strategies")

st.write("#### Dividend capture")

st.write("#### Pre ex-dividend surge")

st.write("#### Post ex-dividend recovery")
