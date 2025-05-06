import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import streamlit as st
import warnings
from utils import draw_header_with_yahoo
from utils import load_symbols

warnings.filterwarnings("ignore")

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


# Write the titles    
st.write("# Stock Market Seasonality Strategies")
st.write("## Sell in May Strategies")

draw_header_with_yahoo(symbol)

st.write("### Strategy overview")
with st.container(key='colored-background-2'):
    st.write("Compare Nov-April vs May-Oct performance for seasonal strategy analysis.")


# ---------- CALCULATION FUNCTIONS ----------

def calculate_returns(sym):
    ticket = yf.Ticker(sym)
    hist = ticket.history(period='max').reset_index()
    hist['month'] = hist.Date.dt.month
    hist['Date'] = pd.to_datetime(hist['Date'])
    hist.set_index('Date', inplace=True)

    def get_first_last_days(group):
        return pd.concat([group.head(1), group.tail(1)])

    monthly_groups = hist.groupby(hist.index.to_period('M'))
    first_last_days = monthly_groups.apply(get_first_last_days).reset_index(level=0, drop=True).reset_index()

    def is_end_of_month(date):
        return date == date + pd.offsets.BusinessMonthEnd(0)

    df = first_last_days[first_last_days['month'].isin([5, 10])]
    df['end_of_month'] = df['Date'].apply(is_end_of_month)

    may = df[df['month'] == 5].reset_index(drop=True).iloc[::2].reset_index(drop=True)
    oct = df[(df['month'] == 10) & df['end_of_month']].reset_index(drop=True)

    may['oct_Close'] = oct['Close']
    may['year'] = may.Date.dt.year
    oct['year'] = oct.Date.dt.year

    df = may.merge(oct[['Close', 'year']], on='year').drop('oct_Close', axis=1)
    df.rename(columns={'Close_x': 'may_Close', 'Close_y': 'oct_Close'}, inplace=True)
    df['MayOct_rtn'] = (df['oct_Close'] - df['may_Close']) / df['may_Close']

    df2 = first_last_days[first_last_days['month'].isin([4, 11])]
    df2['end_of_month'] = df2['Date'].apply(is_end_of_month)

    nov = df2[df2['month'] == 11].reset_index(drop=True).iloc[::2].reset_index(drop=True)
    april = df2[(df2['month'] == 4) & df2['end_of_month']].reset_index(drop=True)

    nov['april_Close'] = april['Close']
    nov['year'] = nov.Date.dt.year
    april['year'] = april.Date.dt.year - 1
    april = april.iloc[1:]

    df2 = nov.merge(april[['Close', 'year']], on='year').drop('april_Close', axis=1)
    df2.rename(columns={'Close_x': 'nov_Close', 'Close_y': 'april_Close'}, inplace=True)
    df2['NovApril_rtn'] = (df2['april_Close'] - df2['nov_Close']) / df2['nov_Close']

    df3 = df2[['year', 'nov_Close', 'april_Close', 'NovApril_rtn']].merge(
        df[['year', 'may_Close', 'oct_Close', 'MayOct_rtn']], on='year'
    )

    return df3

def plot_cumulative_strategy_returns(ticker, start_years_ago=15):
    df = calculate_returns(ticker)
    df = df.sort_values("year").tail(start_years_ago).copy()

    df['NovApril_rtn'].fillna(0, inplace=True)
    df['MayOct_rtn'].fillna(0, inplace=True)

    cum_nov, cum_may = [], []
    r_nov = r_may = 1
    for nov, may in zip(df['NovApril_rtn'], df['MayOct_rtn']):
        r_nov *= (1 + nov)
        r_may *= (1 + may)
        cum_nov.append(r_nov - 1)
        cum_may.append(r_may - 1)

    df['Cum_NovApril'] = cum_nov
    df['Cum_MayOct'] = cum_may

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['year'], y=df['Cum_NovApril'], mode='lines', name='Nov–April'))
    fig.add_trace(go.Scatter(x=df['year'], y=df['Cum_MayOct'], mode='lines', name='May–Oct'))

    fig.update_layout(
        title=f"Cumulative Return of '{ticker}'",
        xaxis_title="Year",
        yaxis_title="Cumulative Return (%)",
        yaxis_tickformat=".0%",
        xaxis=dict(tickmode='linear'),
        template="plotly_white",
        hovermode="x unified"
    )

    return fig

def get_strategy_metrics(df, years=15):
    df = df.tail(years)
    nov_apr_wins = (df['NovApril_rtn'] > df['MayOct_rtn']).sum()
    total = len(df)

    return {
        "Nov to Apr Better (%)": f"{(nov_apr_wins / total) * 100:.2f}%",
        "Nov to Apr Avg Rtn (15Y)": f"{df['NovApril_rtn'].mean():.2%}",
        "May to Oct Avg Rtn (15Y)": f"{df['MayOct_rtn'].mean():.2%}",
        "Nov to Apr Cum Rtn (15Y)": f"{(1 + df['NovApril_rtn']).prod() - 1:.2%}",
        "May to Oct Cum Rtn (15Y)": f"{(1 + df['MayOct_rtn']).prod() - 1:.2%}",
        "Nov to Apr Vol (15Y)": f"{df['NovApril_rtn'].std():.2%}",
        "May to Oct Vol (15Y)": f"{df['MayOct_rtn'].std():.2%}"
    }

# ---------- STREAMLIT APP ----------

with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    years = st.slider("Select number of years to analyze:", min_value=5, max_value=30, value=15)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in the event that you do, no liability will be accepted for any losses.")
    
if symbol:
    try:
        df = calculate_returns(symbol.upper())
        fig = plot_cumulative_strategy_returns(symbol.upper(), start_years_ago=years)
        metrics = get_strategy_metrics(df, years)

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Strategy Metrics")
        with st.container(key='colored-background-4'):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Nov to Apr Better (%)", metrics["Nov to Apr Better (%)"])
                st.metric("Nov to Apr Avg Rtn (15Y)", metrics["Nov to Apr Avg Rtn (15Y)"])
                st.metric("Nov to Apr Cum Rtn (15Y)", metrics["Nov to Apr Cum Rtn (15Y)"])
                st.metric("Nov to Apr Vol (15Y)", metrics["Nov to Apr Vol (15Y)"])

            with col2:
                st.metric("May to Oct Avg Rtn (15Y)", metrics["May to Oct Avg Rtn (15Y)"])
                st.metric("May to Oct Cum Rtn (15Y)", metrics["May to Oct Cum Rtn (15Y)"])
                st.metric("May to Oct Vol (15Y)", metrics["May to Oct Vol (15Y)"])

    except Exception as e:
        st.error(f"Error processing data for '{symbol}': {e}")
