import os, streamlit as st
import pandas as pd
from utils import draw_header_with_yahoo
from utils import load_symbols
import yfinance as yf
import scipy.stats as stats
import plotly.graph_objects as go
from datetime import datetime

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

with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")
    
if params("symbol"):
    symbol = params("symbol")[0].upper()

st.write("# Stock Market Seasonality Strategies")

st.write("## 'Sell in May' Strategies")

draw_header_with_yahoo(symbol)

st.write("### Strategy overview")
with st.container(key='colored-background-2'):
    st.write("We examine the seasonal performance of the stock over a 15 year period comprising comprise various performance metrics split between the two significant investment periods: November to April and May to October. ")

def calculate_returns(sym, verbose=False):
    # Fetch data for Stock Ticker
    ticket = yf.Ticker(sym)

    # Get historical market data
    hist = ticket.history(period='max')
    
    hist = hist.reset_index()
    
    hist['month'] = hist.Date.dt.month
    
    # Ensure 'date' column is in datetime format
    hist['Date'] = pd.to_datetime(hist['Date'])

    # Set 'date' column as index
    hist.set_index('Date', inplace=True)
    
    # Group by month and get the first and last day of each month
    def get_first_last_days(group):
        return pd.concat([group.head(1), group.tail(1)])

    # Group by month and apply the function
    monthly_groups = hist.groupby(hist.index.to_period('M'))
    first_last_days = monthly_groups.apply(get_first_last_days).reset_index(level=0, drop=True)
    first_last_days.reset_index(inplace=True)
    df = first_last_days[(first_last_days['month']==5) |(first_last_days['month']==10)]
    
    # Function to check if a date is the end of the month
    def is_end_of_month(date):
        return date == date + pd.offsets.BusinessMonthEnd(0)

    # Apply the function to create the new column
    df.loc[:,'end_of_month'] = df['Date'].apply(is_end_of_month)
    
    may = df[(df['month']==5)].reset_index()
    # may df shows first and eod, we will skip every other row to only get eod
    may = may.iloc[::2].reset_index(drop=True)

    oct = df[(df['month']==10)].reset_index()
    oct = oct[oct['end_of_month']==True]

    may['oct_Close'] = oct['Close']
    may['year'] = may.Date.dt.year
    oct['year'] = oct.Date.dt.year
    
    df = may.merge(oct[['Close','year']],on='year')
    df.drop('oct_Close', axis=1, inplace=True)

    df.rename(columns = {'Close_x': 'may_Close',
                           'Close_y':'oct_Close' },inplace=True)

    df['MayOct_rtn'] = (df['oct_Close'] - df['may_Close']) / df['may_Close']
    
    ######################################
    ##  Getting Nov to Apr returns      #
    ######################################
    
    df2 = first_last_days[(first_last_days['month']==4) |(first_last_days['month']==11)]
    df2.loc[:, 'end_of_month'] = df2['Date'].apply(is_end_of_month)
    
    # Create nov
    nov = df2[(df2['month']==11)].reset_index()
    nov = nov.iloc[::2].reset_index(drop=True)
    
    # Create april
    april = df2[(df2['month']==4)].reset_index()
    april = april[april['end_of_month']==True]

    # Create the april_Close and year column for nov
    nov['april_Close'] = april['Close']
    nov['year'] = nov.Date.dt.year
    
    # Create the year column for april
    april['year'] = april.Date.dt.year

    # Remove the first row
    april = april.drop(april.index[0])

    # Decrease the year by one for the later merge
    # This is so you can compare data of the following year for April, for example Nov 1st 2022 and April 30th 2023
    april['year'] = april['year'] - 1
    
    # Merge nov and april on year
    df2 = nov.merge(april[['Close','year']],on='year')

    # Create april_Close column
    df2.drop('april_Close', axis=1, inplace=True)
    df2.rename(columns = {'Close_x': 'nov_Close',
                               'Close_y':'april_Close' },inplace=True)
    
    # Calculate the return
    df2['NovApril_rtn'] = (df2['april_Close'] - df2['nov_Close']) / df2['nov_Close']
    
    ##############################################
    ##  Merge May/Oct and Nov/Apr returns      #
    ##############################################
    
    df3 = df2[['year','nov_Close','april_Close','NovApril_rtn']].merge(df[['year','may_Close','oct_Close','MayOct_rtn']],on='year')
    
    NovAprBetter = df3[df3['NovApril_rtn'] > df3['MayOct_rtn']]['year'].count()
    total = df3['year'].count()
    
    pct = NovAprBetter / total

    if verbose: #if you want to print the sentence at the bottom set verbose = true 
        print(f"Nov to April return for {sym} was better {NovAprBetter} out of {total}, {pct:.2f}")

#    print("Nov to April return for "+ sym + " was better " + str(NovAprBetter) + " out of " + str(total) + " , " + str(pct) )

    return df3

def plot_cumulative_strategy_returns(ticker, start_years_ago=15):
    df = calculate_returns(ticker)
    df = df.sort_values("year")

    # Filter for the last N years
    current_year = datetime.today().year
    start_year = current_year - start_years_ago
    df = df.tail(start_years_ago).copy()

    # Fill missing values
    df['NovApril_rtn'].fillna(0, inplace=True)
    df['MayOct_rtn'].fillna(0, inplace=True)

    # Create new columns for total compounded return like in analyze_tickers3
    cum_nov = []
    cum_may = []
    running_nov = 1
    running_may = 1
    for nov_rtn, may_rtn in zip(df['NovApril_rtn'], df['MayOct_rtn']):
        running_nov *= (1 + nov_rtn)
        running_may *= (1 + may_rtn)
        cum_nov.append(running_nov - 1)
        cum_may.append(running_may - 1)

    df['Cum_NovApril'] = cum_nov
    df['Cum_MayOct'] = cum_may

    # Plotting
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

st.write("### Does the strategy work for this stock?")
with st.container(key='colored-background-3'):

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
            fig = plot_cumulative_strategy_returns(symbol.upper(), start_years_ago=15)
            st.plotly_chart(fig, use_container_width=True)

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
