import os, streamlit as st
import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt
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

# Draw the tickers list on the sidebar
with st.sidebar:
    symbol = st.selectbox("Search for a Stock Ticker", tickers, index=tickers_idx)
    st.write("**Disclaimer:** The following information is provided for informational purposes only and is not investment advice. You should not make investments based on this advice and in the event that you do, no liability will be accepted for any losses.")

# Write the titles    
st.write("# Stock Market Seasonality Strategies")
st.write("## Dividend Strategies")

draw_header_with_yahoo(symbol)

st.write("### Strategy overview")
with st.container(key='colored-background-2'):
    st.write("This strategy focuses on identifying stocks which exhibit abnormal price and trading volume volatility during this dividend declaration to payment period. We test a 'dividend capture' strategy, buying the day before the ex-dividend date and selling the day after.")

#st.write("### Does the strategy work for this stock?")
#with st.container(key='colored-background-3'):



POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

client = RESTClient("Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8")

details = client.get_ticker_details(symbol)    

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
                "AvgPriceDiv": None,
                "AvgPriceNonDiv": None,
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

long_term_volume = analyze_volume_spike(symbol)

st.write("### Long-Term Dividend Strategies")
with st.container(key='colored-background-3'):
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

    long_term_return = analyze_dividend_price_behavior(symbol)

    if long_term_return is not None:
        if long_term_return["AvgPriceNonDiv"] >= long_term_return["AvgPriceDiv"]:
            st.write(f"The average price is less during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
            st.write("Consider buying during this time.")
        else:
            st.write(f"The average price is more during the dividend period (+-3 days around the ex-dividend date to dividend pay date).")
            st.write("Consider waiting until this time is over.")
        
        st.write(f" - Average Price in Dividend Period (excluding dividend): {long_term_return["AvgPriceDiv"]}")
        st.write(f" - Average Price in Non-Dividend Period: {long_term_return["AvgPriceNonDiv"]}")
    else: 
        st.write("No dividends in period.")

def calculate_and_plot_average_return(stock_data, df_events, window=1):
    results = []
    valid_events = df_events.dropna(subset=["ex_dividend_date"]).copy()
    valid_events = valid_events[valid_events["ex_dividend_date"] <= pd.Timestamp.today()]

    for _, row in valid_events.iterrows():
        ann_date = pd.Timestamp(row["ex_dividend_date"])
        if ann_date not in stock_data.index:
            future = stock_data.index[stock_data.index > ann_date]
            if not future.empty:
                ann_date = future[0]
            else:
                continue
        idx = stock_data.index.get_indexer([ann_date])[0]
        if idx < window or idx + window >= len(stock_data):
            continue
        price_before = stock_data.iloc[idx - window]["Close"][0]
        price_after = stock_data.iloc[idx + window]["Close"][0]
        dividend = row["cash_amount"]
        return_pct = ((price_after - price_before) / price_before) + ( dividend / price_before) * 100
        #return_pct = (price_after - price_before) / price_before * 100
    
        results.append({
            "Ex_Dividend_Date": row["ex_dividend_date"],
            "Dividend": row["cash_amount"],
            "Buy Price": price_before,
            "Sell Price": price_after,
            "Return_%": return_pct
        })


    returns_df = pd.DataFrame(results)
    
    avg_return = returns_df["Return_%"].mean()
    print(f"Average Return per Event: {avg_return:.2f}%")

    # Plot
    returns_df = returns_df.sort_values("Ex_Dividend_Date")
    returns_df["Ann_Label"] = returns_df["Ex_Dividend_Date"].dt.strftime('%b %Y')
    tick_indices = returns_df.index[::4]
    tick_labels = returns_df.loc[tick_indices, "Ann_Label"]

    plt.figure(figsize=(12, 6))
    plt.plot(returns_df["Ex_Dividend_Date"], returns_df["Return_%"], marker='o')
    plt.axhline(0, color='red', linestyle='--', label='Break-even')
    plt.xticks(ticks=returns_df.loc[tick_indices, "Ex_Dividend_Date"], labels=tick_labels, rotation=45)
    plt.title("Returns per Dividend Event")
    plt.xlabel("Ex-Dividend Date")
    plt.ylabel("Return (%)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    
    # For each dividend event 
    # 	Calculate:
    #     Price return = (Sell price − Buy price) / Buy price
    #     Total return = Price return + (Dividend / Buy price)

    return returns_df

st.write("### Short-Term Dividend Strategies")
with st.container(key='colored-background-4'):
    st.write("#### Dividend capture")
    st.write("We evaluate the effects of buying the stock one day before the ex-dividend date and selling one day after over a 10-year period.")

    st.write("##### Results")

    start_date = "2015-01-01"
    end_date = "2026-12-31"

    # Load stock data from Yahoo
    stock_data = yf.download(symbol, start=start_date, end=end_date)
    stock_data = stock_data[["Close"]].dropna()
    stock_data.index = pd.to_datetime(stock_data.index)

    # Load dividends metadata from Polygon.io
    dividends_poly = client.list_dividends(ticker=symbol, limit=100)
    df_events = pd.DataFrame([{
        'declaration_date': d.declaration_date,
        'record_date': d.record_date,
        'pay_date': d.pay_date,
        'ex_dividend_date': d.ex_dividend_date,
        'cash_amount': d.cash_amount
    } for d in dividends_poly])

    # Create our events table 
    df_events['declaration_date'] = pd.to_datetime(df_events['declaration_date'])
    df_events['record_date'] = pd.to_datetime(df_events['record_date'])
    df_events['pay_date'] = pd.to_datetime(df_events['pay_date'])
    df_events['ex_dividend_date'] = pd.to_datetime(df_events['ex_dividend_date'])

    # Return data for this stock 
    returns_df = calculate_and_plot_average_return(stock_data, df_events)

    # Confirm the average return 
    avg_return = returns_df["Return_%"].mean()
    st.write(f"Average Return: {avg_return:.2f}%")

    # Calculate the cumulative return
    initial_investment = 1000
    returns_df = returns_df.sort_values("Ex_Dividend_Date").reset_index(drop=True)
    returns_df["Return_Multiplier"] = 1 + (returns_df["Return_%"] / 100)
    returns_df["Capital"] = initial_investment * returns_df["Return_Multiplier"].cumprod()
    returns_df["Ann_Label"] = returns_df["Ex_Dividend_Date"].dt.strftime('%b %Y')

    # Display the cumulative return
    cum_return = returns_df["Capital"].iloc[-1]
    cum_return_pct = ((cum_return - initial_investment) / initial_investment) * 100

    st.write(f"Cumulative Return: {cum_return_pct:.2f}%")

    st.write("##### Returns Per Event")

    # Plot the returns
    returns_df = returns_df.sort_values("Ex_Dividend_Date")
    returns_df["Ann_Label"] = returns_df["Ex_Dividend_Date"].dt.strftime('%b %Y')
    tick_indices = returns_df.index[::4]
    tick_labels = returns_df.loc[tick_indices, "Ann_Label"]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(returns_df["Ex_Dividend_Date"], returns_df["Return_%"], marker='o')
    ax.axhline(0, color='red', linestyle='--', label='Break-even')
    ax.set_xticks(returns_df.loc[tick_indices, "Ex_Dividend_Date"])
    ax.set_xticklabels(tick_labels, rotation=45)
    ax.set_title("Returns per Dividend Event")
    ax.set_xlabel("Ex-Dividend Date")
    ax.set_ylabel("Return (%)")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

    # Show in Streamlit
    st.pyplot(fig)

    st.write("##### Cumulative Return")
    returns_df = returns_df.sort_values("Ex_Dividend_Date").reset_index(drop=True)
    returns_df["Return_Multiplier"] = 1 + (returns_df["Return_%"] / 100)
    returns_df["Capital"] = initial_investment * returns_df["Return_Multiplier"].cumprod()
    returns_df["Ann_Label"] = returns_df["Ex_Dividend_Date"].dt.strftime('%b %Y')

    tick_indices = returns_df.index[::4]
    tick_labels = returns_df.loc[tick_indices, "Ann_Label"]
    tick_dates = returns_df.loc[tick_indices, "Ex_Dividend_Date"]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(returns_df["Ex_Dividend_Date"], returns_df["Capital"], marker='o')
    ax.axhline(initial_investment, color='gray', linestyle='--', label='Initial Capital')

    ax.set_xticks(tick_dates)
    ax.set_xticklabels(tick_labels, rotation=45)
    ax.set_title("Cumulative Portfolio Growth")
    ax.set_xlabel("Ex-Dividend Announcement Date")
    ax.set_ylabel("Capital ($)")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

    # Render in Streamlit
    st.pyplot(fig)

    st.write("##### Dividend History")

    st.dataframe(
        df_events
            .rename(columns={"declaration_date":"Declaration Date", "record_date":"Record Date", "pay_date":"Pay Date", "ex_dividend_date":"Ex-Dividend Date"})
    )


