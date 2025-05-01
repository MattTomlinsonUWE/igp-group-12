import os, streamlit as st
from utils import draw_header_with_yahoo
from utils import load_symbols
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from prophet import Prophet
from datetime import datetime, timedelta
import requests
from scipy import stats
import math

# Step 2 - Set up the UI 
st.set_page_config(
    page_title="Stock Seasonality Application - Easter Holiday Strategies",
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

# # Retrieve symbol from session state
# if st.session_state['ticker'] is not None: 
#     symbol = st.session_state['ticker']

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
st.write("## 'Easter Holiday' Strategies:")

draw_header_with_yahoo(symbol)

st.write("### Strategy overview")
with st.container(key='colored-background-2'):
    st.write("Buy the stock before Easter holiday and sell after Easter holiday. As per research data Easter always falls on a Sunday between March 22 and April 25, inclusively.")
    st.write("Hence in this analysis, pattern of returns has been observed between 22nd March & 25th April between 2004 to 2025.")

# Fetch stock data
def fetch_stock_data(ticker):

    start_date = datetime(2004, 1, 1)
    end_date = datetime.today()
    data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
    data.reset_index(inplace=True)
    data.set_index(['Date'])

    # Calculate Daily returns
    data['Daily_Return'] = data['Adj Close'].pct_change()
    data['Cumulative_Return'] = (1 + data['Daily_Return']).cumprod()

    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]  # Flatten column names
     #st.write(data.columns)
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    filtered_data = pd.concat([
        data[(data['Date'] >= pd.Timestamp(f'{year}-03-22')) & (data['Date'] <= pd.Timestamp(f'{year+1}-04-25'))]
        for year in range(2004, 2025)
    ])

    return filtered_data, data

# Calculate annualized returns
def calculate_annualized_return(selected_period):
    # Group by year and calculate cumulative return for each April
    annual_returns = selected_period.groupby(selected_period['Date'].dt.year).apply(
        lambda x: (1 + x['Daily_Return']).prod() - 1
    )
    
    # Calculate mean return across all years
    mean_return = annual_returns.mean()
    
    # Annualize the return (assuming 30-day period)
    annualized_return = (1 + mean_return) ** (365/30) - 1
    
    return annualized_return * 100  

def annualized_returns(returns):
    # Convert returns to growth factors
    growth_factors = [(1 + r/100) for r in returns]
    cumulative_factor = math.prod(growth_factors)

    # Number of years
    n = len(returns)

    # Calculate the annualized return (in decimal form)
    annualized_return = cumulative_factor**(1/n) - 1

    # Convert to percentage
    annualized_return_percentage = annualized_return * 100

    return annualized_return_percentage

# Yearly cumulative returns
def calculate_yearly_returns(filtered_data):

    yearly_returns = (
        filtered_data.groupby(filtered_data['Date'].dt.year)['Daily_Return']
        .apply(lambda x: (1 + x).prod() - 1) * 100
    )
    
    return yearly_returns.reset_index(name='Return(%)')

##Stats
def calculate_return_stats(df, annualized_return, cumulative_return):
   
    avg_return=df['Return(%)'].mean()
    median_return=df['Return(%)'].median()
    percent_positive=(df['Return(%)'] > 0).mean() * 100
    avg_positive_return=df.loc[df['Return(%)'] > 0, 'Return(%)'].mean()
    avg_negative_return=df.loc[df['Return(%)'] < 0, 'Return(%)'].mean()
    best_return=df['Return(%)'].max()
    worst_return=df['Return(%)'].min()
    std_deviation=df['Return(%)'].std()
   
    st.subheader("Return statistics")
    with st.container(key='colored-background-3'):
        st.write("Return statistics can provide insights into past investment performance, which can help investors make more informed decisions about future investments.")
        st.write("By analyzing historical returns, one can gain a better understanding of seasonality effects during Easter holiday.")
    
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Average Return", f"{avg_return:.2f}%")
        col2.metric("Median Return", f"{median_return:.2f}%")
        col3.metric("Percent Positive", f"{percent_positive:.2f}%")
        col4.metric("Annualized Return", f"{annualized_return:.2f}%")
        col5.metric("Cumulative Return", f"{cumulative_return:.2f}%")

        col6, col7, col8, col9 = st.columns(4)
        col6.metric("Avg Positive Return", f"{avg_positive_return:.2f}%")
        col7.metric("Avg Negative Return", f"{avg_negative_return:.2f}%")
        col8.metric("Best Return", f"{best_return:.2f}%")
        col9.metric("Worst Return", f"{worst_return:.2f}%")
 
selected_period, data = fetch_stock_data(symbol)
annual_returns= calculate_yearly_returns(selected_period)
# st.write(data)
avgannualreturns = annual_returns['Return(%)'].values
annualized_return = annualized_returns(avgannualreturns)
#st.header("% Cumulative Returns")
cumulative_return = data['Cumulative_Return'].iloc[-1]
calculate_return_stats(annual_returns, annualized_return, cumulative_return)


# Display in Streamlit
st.subheader("% Annual returns")
with st.container(key='colored-background-4'):
    st.write("Below graph displays %Annual Returns during Easter period.")
    fig = px.bar(annual_returns, x='Date', y='Return(%)', labels={'Date': 'Year', 'Return(%)': 'Annual Return (%)'}, text=[f"{x:.1f}%" for x in annual_returns['Return(%)']])
    # Customize text position and appearance
    fig.update_traces(
        textposition='outside',
        textfont_size=12,
        #marker_color=np.where(annual_returns['Return (%)'] > 0, 'green', 'red')
    )
    # Improve layout
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        yaxis_tickformat='.1f%',
        hovermode='x'
    )
    st.plotly_chart(fig)


# Annualized Standard Deviation
std_dev = selected_period['Daily_Return'].std() * np.sqrt(252)  # Trading days

# Sharpe Ratio (assuming risk-free rate = 0)
sharpe_ratio = (annualized_return.mean() / 100) / (selected_period['Daily_Return'].std() * np.sqrt(252))

# Sortino Ratio (only downside deviation)
downside_returns = selected_period[selected_period['Daily_Return'] < 0]['Daily_Return']
sortino_ratio = (annualized_return.mean() / 100) / (downside_returns.std() * np.sqrt(252))

st.subheader("Risk Metrics:")
with st.container(key='colored-background-5'):
    st.write("Risk-adjusted metrics help investors understand not just how much return an investment generated, but how much risk was taken to achieve it.")
    st.write(f"**Standard Deviation (Annualized):** {std_dev:.2f}")
    st.write(f"**Sharpe Ratio (Risk-Free=0):** {sharpe_ratio:.2f}")
    st.write(f"**Sortino Ratio:** {sortino_ratio:.2f}")

    #st.write(selected_period)

    # Compute EMAs
    data['EMA_50'] = data['Adj Close'].ewm(span=50, adjust=False).mean()
    data['EMA_100'] = data['Adj Close'].ewm(span=100, adjust=False).mean()

# Plot in Streamlit
st.subheader("20-Year Price with 50 & 100 EMA:")
with st.container(key='colored-background-6'):
    st.write("Moving averages are a staple of technical analysis because they help investors determine what is happening in the market by smoothing out price data and filtering out short-term volatility. Traders use them to determine if a market is trending and, if it is trending, as dynamic support and resistance levels.")
    fig = px.line(
        data,
        x='Date',
        y=['Adj Close', 'EMA_50', 'EMA_100'],    
        title=f"{symbol} Price & EMAs"
    )
    st.plotly_chart(fig)

    # One-sample T-test (H₀: Mean return = 0)
    t_stat, p_value = stats.ttest_1samp(selected_period['Daily_Return'], popmean=0)

    # Display results
st.subheader("Statistical Significance:")
with st.container(key='colored-background-7'):
    st.write("his analysis helps in validating robustness and testing hypothesis. In this case it validates if the returns are significant.")
    st.write("T-Statistics: Used to test hypotheses about returns, ensuring statistical significance.")
    st.write("P-Value: Indicates the probability of observing results under a null hypothesis, aiding decision-making. Low p-value (<0.05) confirms statistical significance.") 
    st.subheader(f"**T-statistic:** {t_stat:.2f}")
    st.subheader(f"**P-value:** {p_value:.4f}")

    if p_value < 0.05:
        st.success("Reject H₀: Returns are statistically significant (≠ 0).")
    else:
        st.error("Fail to reject H₀: Returns are not significantly different from 0.")

# Forecasting with Prophet
st.subheader("Stock Price Prediction using Prophet:")
with st.container(key='colored-background-8'):
    st.write("The prophet is an algorithm to build forecasting models for time series data. It is unlike the traditional approach as it tries to fit additive regression models. Moreover, it is very flexible when it comes to the data that is fed to the algorithm.")
    st.write("A forecasting tool that models time-series data, capturing seasonality and trends. It’s a Facebook’s time-series forecasting tool which handles missing data, seasonality and trends. It’s good for intuitive, automated stock trend predictions.")
    df = data[['Date', 'Close']]
    df.columns = ['ds', 'y']

    # Train Prophet Model
    model = Prophet()
    model.fit(df)

    # Make predictions
    future = model.make_future_dataframe(periods=30, freq='M')  # Set frequency to monthly
    forecast = model.predict(future)

    # Merge actual and predicted data
    forecast_merged = forecast[['ds', 'yhat']].merge(df, on='ds', how='left')
    forecast_merged.rename(columns={'y': 'Actual Price', 'yhat': 'Predicted Price', 'ds': 'Year'}, inplace=True)

    # Plot actual vs predicted prices
    fig_forecast = px.line(forecast_merged, x='Year', y=['Actual Price', 'Predicted Price'], 
                        labels={'value': 'Stock Price', 'variable': 'Legend'},
                        title="Actual vs Predicted Prices",
                        color_discrete_map={'Actual Price': 'royalblue', 'Predicted Price': 'orange'})
    fig_forecast.update_layout(legend_title_text='Stock Prices')
    fig_forecast.update_xaxes(nticks=20, tickformat="%Y")  # Increase number of x-axis ticks
    st.plotly_chart(fig_forecast)
