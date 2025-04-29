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
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in teh event that you do, no liability will be accepted for any losses.")
    
if params("symbol"):
    symbol = params("symbol")[0].upper()

st.write("# Stock Market Seasonality Strategies")

draw_header_with_yahoo(symbol, True)

st.write("## 'Easter Holiday' Strategies:")


# Fetch stock data
def fetch_stock_data(ticker, start_filter, end_filter):

    start_date = datetime(2004, 1, 1)
    end_date = datetime.today()
    data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
    data.reset_index(inplace=True)
    data.set_index(['Date'])
    data['Daily_Return'] = data['Adj Close'].pct_change()
    #
    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]  # Flatten column names
    
    #st.write(data.columns)
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')

    filtered_data = data[
        (data['Date'].dt.strftime('%m-%d') >= start_filter) &  # From April 1
        (data['Date'].dt.strftime('%m-%d') <= end_filter)    # To July 15
    ].copy()

    return filtered_data, data

# Calculate annualized returns
start_filter = '04-01'
end_filter = '04-30'
selected_period, data = fetch_stock_data(symbol, start_filter, end_filter)

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

    # Calculate cumulative growth factor by multiplying all factors together    
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
    yearly_returns = filtered_data.groupby(filtered_data['Date'].dt.year).apply(
        lambda x: (1 + x['Daily_Return']).prod() - 1
    ) * 100  
    
    return yearly_returns.reset_index(name='Return(%)')

##Stats
def calculate_return_stats(df, annualized_return):
   
    avg_return=df['Return(%)'].mean()
    median_return=df['Return(%)'].median()
    percent_positive=(df['Return(%)'] > 0).mean() * 100
    avg_positive_return=df.loc[df['Return(%)'] > 0, 'Return(%)'].mean()
    avg_negative_return=df.loc[df['Return(%)'] < 0, 'Return(%)'].mean()
    best_return=df['Return(%)'].max()
    worst_return=df['Return(%)'].min()
    std_deviation=df['Return(%)'].std()

   
    st.header("Return Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average Return", f"{avg_return:.2f}%")
    col2.metric("Median Return", f"{median_return:.2f}%")
    col3.metric("Percent Positive", f"{percent_positive:.2f}%")
    col4.metric("Standard Deviation", f"{std_deviation:.2f}%")

    col5, col6, col7, col8, col9 = st.columns(5)
    col5.metric("Avg Positive Return", f"{avg_positive_return:.2f}%")
    col6.metric("Avg Negative Return", f"{avg_negative_return:.2f}%")
    col7.metric("Best Return", f"{best_return:.2f}%")
    col8.metric("Worst Return", f"{worst_return:.2f}%")
    col9.metric("Annualized Return", f"{annualized_return:.2f}%")
 
    
annual_returns= calculate_yearly_returns(selected_period)
avgreturns = annual_returns['Return(%)'].values
annualized_return = annualized_returns(avgreturns)
calculate_return_stats(annual_returns, annualized_return)

st.header("% Annual Returns")
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

# Display in Streamlit
st.header("Risk Metrics")
st.subheader(f"**Standard Deviation (Annualized):** {std_dev:.2f}")
st.subheader(f"**Sharpe Ratio (Risk-Free=0):** {sharpe_ratio:.2f}")
st.subheader(f"**Sortino Ratio:** {sortino_ratio:.2f}")


# Compute EMAs
data['EMA_50'] = data['Adj Close'].ewm(span=50, adjust=False).mean()
data['EMA_100'] = data['Adj Close'].ewm(span=100, adjust=False).mean()

# Plot in Streamlit
st.header("20-Year Price with 50 & 100 EMA")
fig = px.line(
    data,
    y=['Adj Close', 'EMA_50', 'EMA_100'],
    title=f"{symbol} Price & EMAs"
)
st.plotly_chart(fig)


# One-sample T-test (H₀: Mean return = 0)
t_stat, p_value = stats.ttest_1samp(selected_period['Daily_Return'], popmean=0)

# Display results
st.header("Statistical Significance")
st.subheader(f"**T-statistic:** {t_stat:.2f}")
st.subheader(f"**P-value:** {p_value:.4f}")

if p_value < 0.05:
    st.success("Reject H₀: Returns are statistically significant (≠ 0).")
else:
    st.error("Fail to reject H₀: Returns are not significantly different from 0.")



# Forecasting with Prophet
st.header("Stock Price Prediction using Prophet")
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


