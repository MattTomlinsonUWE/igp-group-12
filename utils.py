import os, streamlit as st
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pandas import json_normalize
from polygon import RESTClient
import yfinance as yf
import locale
from datetime import datetime
import plotly.graph_objects as go


#locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

@st.cache_data
def draw_header(symbol):
    #TO DO - move this to the environment
    POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

    client = RESTClient("Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8")

    details = client.get_ticker_details(symbol)

    market_cap = details.market_cap
    shares_outstanding = details.share_class_shares_outstanding

    snapshot = client.get_snapshot_all(market_type='stocks', tickers=symbol)

    yesterday_change = 0
    
    yesterday_high = snapshot[0].prev_day.high
    yesterday_low = snapshot[0].prev_day.low
    yesterday_open = snapshot[0].prev_day.open
    yesterday_close = snapshot[0].prev_day.close
    yesterday_change =  yesterday_close - yesterday_open
    yesterday_change_pct = ((yesterday_close - yesterday_open) / yesterday_open) * 100

    yesterday_volume = snapshot[0].prev_day.volume

    # Get the most recent dividend data
    divData = []
    dividendHistory = []
    counter = 0

    latest_dividend = 0
    ex_dividend_date = ""
    dividend_pay_date = ""

    for t in client.list_dividends(ticker=symbol, limit=1, order="asc"):
    
        #add object to list
        divData.append(t)
    
        latest_dividend = t.cash_amount
        ex_dividend_date = t.ex_dividend_date
        dividend_pay_date = t.pay_date
    
        counter += 1

    # Assuming annual dividend is 4x the latest dividend (quarterly payout assumption)
    annual_dividend = latest_dividend * 4  

    # Calculate dividend yield
    if yesterday_close > 0:
        dividend_yield = (annual_dividend / yesterday_close) * 100
    else:
        dividend_yield = 0  # Avoid division by zero

    bid_price = 0
    sell_price = 0
    change_price = 0
    change_price_pct = 0

    # Calculate the date range (past 1 year)
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')

    # Fetch the last year's daily aggregate data
    aggs = client.get_aggs(ticker=symbol, multiplier=1, timespan="day", from_=start_date, to=end_date)

    priceData = pd.DataFrame(aggs)

    year_high = priceData['close'].max()
    year_low = priceData['close'].min()

    # Get the average trading volume
    volumes = 0
    avg_volume = 0

    # Define the date range (last 10 days)
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=10)).strftime('%Y-%m-%d')

    # Fetch aggregate (OHLCV) data for the last 10 days
    aggs = client.get_aggs(ticker=symbol, multiplier=1, timespan="day", from_=start_date, to=end_date)

    for day in aggs: 
        volumes = volumes + aggs[0].volume
    
    # Calculate the average volume over 10 days
    if volumes:
        avg_volume = volumes / len(aggs)

    # Get the financial fundamentals
    data = []

    # request financial statement data 
    for t in client.vx.list_stock_financials(ticker=symbol, filing_date_gte='2022-01-01', limit=1, order="desc"):
        data.append(t)

    pe_ratio = 0
    rps = 0
    eps = 0
    revenue = 0
    filing_date = ""
    net_income = 0

    if len(data) > 0:
        eps = data[0].financials.income_statement.basic_earnings_per_share.value
        filing_date = data[0].filing_date
        revenue = data[0].financials.income_statement.revenues.value
        net_income = data[0].financials.comprehensive_income.comprehensive_income_loss_attributable_to_parent.value
        revenue = data[0].financials.income_statement.revenues.value

    # Calculate the P/E Ratio
    if eps is not None and eps > 0:
        pe_ratio = yesterday_close / eps

    # Calculate the RPS
    if revenue is not None and revenue > 0:
        rps =  revenue / shares_outstanding

    table_1_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
            color:#000;
        }
    </style>

    <table>
        <tr>
            <td><strong>Yesterday Open<strong></td>
            <td>""" + str(yesterday_open) + """</td>
        </tr>
        </tr>
        <tr>
            <td><strong>Yesterday Close<strong></td>
            <td>""" + str(yesterday_close) + """</td>
        </tr>
        <tr>
            <td><strong>Yesterday High<strong></td>
            <td>""" + str(yesterday_high) + """</td>
        </tr>
        <tr>
            <td><strong>Yesterday Low<strong></td>
            <td>""" + str(yesterday_low) + """</td>
    </table>
    """

    table_2_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
        }
    </style>

    <table>
        <tr>
            <td><strong>Volume<strong></td>
            <td>""" + str(yesterday_volume) + """</td>
        </tr>
        <tr>
            <td><strong>Div Yield (%)<strong></td>
            <td>""" + str(round(dividend_yield, 2)) + """</td>
        </tr>
        <tr>
            <td><strong>Year High<strong></td>
            <td>""" + str(year_high) + """</td>
        </tr>
        <tr>
            <td><strong>Year Low<strong></td>
            <td>""" + str(year_low) + """</td>
        </tr>
    </table>
    """

    # Set up the top column with company details
    col1, col2 = st.columns([1,9])

    with col1:
        try:
            if(details.branding.icon_url):
                st.image(details.branding.icon_url + '?apiKey=' + POLYGON_API_KEY, width=100)
        except Exception as e:
            st.write(" ")
    with col2:
        st.header(details.name)
        st.markdown("**Symbol:** " + symbol)

    # Set up the middle columns with financials
    col11, col12, col13, col14, col15 = st.columns(5)
    with col11:
        st.markdown(f"**Buy:**")
        st.markdown(f'<p style="font-size:28px">TO DO</p>', unsafe_allow_html=True)
    with col12:
        st.markdown("**Sell:** ")
        st.markdown(f'<p style="font-size:28px">TO DO</p>', unsafe_allow_html=True)
    with col13:
        st.markdown("**Yesterday Price Change:** ")
        if yesterday_change >= 0:
            st.markdown(f'<p style="font-size:28px;color:green">${yesterday_change:.2} ({yesterday_change_pct:.2}%)</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="font-size:28px;color:red">${yesterday_change:.2} (-{yesterday_change_pct:.2}%)</p>', unsafe_allow_html=True)

    with col14:
        st.markdown(table_1_html_code, unsafe_allow_html=True)
    with col15:
        st.markdown(table_2_html_code, unsafe_allow_html=True)

    # Set up the tabs
    tab1, tab3, tab4  = st.tabs(["Overview", "Dividend", "Chart"])

    table_3_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
        }
    </style>

    <table>
        <tr>
            <td><strong>Ex-dividend date<strong></td>
            <td>""" + str(ex_dividend_date) + """</td>
        </tr>
        <tr>
            <td><strong>Pay date<strong></td>
            <td>""" + str(dividend_pay_date) + """</td>
        </tr>
        <tr>
            <td><strong>Total dividends year to date<strong></td>
            <td>TO DO</td>
        </tr>
        <tr>
            <td><strong>Dividend yield (%)<strong></td>
            <td>""" + str(round(dividend_yield, 2)) + """</td>
        </tr>
    </table>
    """

    table_4_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
        }
    </style>

    <table>
        <tr>
            <td><strong>Filing Date<strong></td>
            <td>""" + filing_date + """</td>
        </tr>
        <tr>
            <td><strong>Revenue<strong></td>
            <td>""" + f'{revenue:,}' + """</td>
        </tr>
        <tr>
            <td><strong>Net Income<strong></td>
            <td>""" + f'{net_income:,}' + """</td>
        </tr>
        <tr>
            <td><strong>PE Ratio<strong></td>
            <td>""" + str(round(dividend_yield, 2)) + """</td>
        </tr>
        <tr>
            <td><strong>Earnings per Share<strong></td>
            <td>""" + str(round(eps, 2)) + """</td>
        </tr>
        <tr>
            <td><strong>Revenue per Share<strong></td>
            <td>""" + str(round(rps, 2)) + """</td>
        </tr>
    </table>
    """

    with tab1:
        st.subheader('Last Financials')

        st.markdown(table_4_html_code, unsafe_allow_html=True)

    with tab3:

        if not symbol.strip():
            st.error("Please select a symbol")
        else:
            try:
                st.subheader('Latest Dividend Information')

                st.markdown(table_3_html_code, unsafe_allow_html=True)

                divData = []
                dividendHistory = []
                counter = 0

                # paginated end point
                for t in client.list_dividends(ticker=symbol, limit=1000):
    
                    #add object to list
                    divData.append(t)
    
                    #create tuple and add to list
                    tempTuple = (datetime.strptime(t.ex_dividend_date, '%Y-%m-%d'),
                     t.cash_amount)
                    dividendHistory.append(tempTuple)

                    counter += 1

                divTimeSeries = pd.DataFrame(dividendHistory, columns =['Date', 'Dividend'])

                divTimeSeries = divTimeSeries.set_index('Date')

                st.write(divTimeSeries)

            except Exception as e:
                st.exception(f"Exception: {e}")
    
    with tab4:
        if not symbol.strip():
            st.error("Please select a symbol")
        else:
            try:
                dataRequest = client.list_aggs(
                    ticker = symbol,
                    multiplier = 1,
                    timespan = "day",
                    from_ = "2024-01-01",
                    to = "2024-04-29"
                )
                chart_data = pd.DataFrame(dataRequest)
    
                chart_data['date_formatted'] = chart_data['timestamp'].apply(
                              lambda x: pd.to_datetime(x*1000000))
      
                st.line_chart(chart_data, x="date_formatted",y="close")
    
            except Exception as e:
                st.exception(f"Exception: {e}") 


def draw_header_with_yahoo(symbol,minimal=False):

    ticker = yf.Ticker(symbol)

    stock_name = ticker.info.get('longName')
    market_cap = ticker.info.get("marketCap")
    current_price = ticker.info.get("currentPrice")
    shares_outstanding = ticker.info.get("sharesOutstanding")
    year_high = ticker.info.get('fiftyTwoWeekHigh', None)
    year_low = ticker.info.get('fiftyTwoWeekLow', None)

    #Initial Variables
    dividend = 0
    revenue = 0
    net_income = 0
    pe_ratio = 0
    eps = 0
    rps = 0
    ex_dividend_date = None
    dividend_pay_date = None
    filing_date = None
    
    # Dividend yield is usually a decimal (e.g., 0.015 = 1.5%)
    dividend_yield = ticker.info.get('dividendYield', None)

    if dividend_yield is not None:
        dividend_yield = round(dividend_yield * 100, 2)  # Convert to percentage

    # Get yesterday's date
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')

    # Download 2 days of data to account for weekends/holidays
    data = yf.download(symbol, period="5d", interval="1d", progress=False)

    # Filter for the most recent valid trading day (yesterday or prior)
    data = data[data.index.date < datetime.now().date()]

    if data.empty:
        print("No data found.")
        return None

    # Get the last row (most recent trading day before today)
    last_row = data.iloc[-1]

    yesterday_open = float(last_row['Open'].iloc[0])
    yesterday_close = float(last_row['Close'].iloc[0])
    yesterday_high = float(last_row['High'].iloc[0])
    yesterday_low = float(last_row['Low'].iloc[0])
    yesterday_volume = float(last_row['Volume'].iloc[0])

    yesterday_change = data['Close'].iloc[-1] - data['Close'].iloc[-2]
    yesterday_change = yesterday_change.iloc[0]
    yesterday_change_pct = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
    yesterday_change_pct = yesterday_change_pct.iloc[0]

    dividends = ticker.dividends

    # Check to be sure that we have dividend data
    if len(dividends) > 0:
        dividend = dividends.iloc[-1]

        div_table = pd.DataFrame({
            "Pay Date": dividends.index,
            "Amount": dividends.values
        })

        div_table["Pay Date"] = pd.to_datetime(div_table["Pay Date"]).dt.date
        div_table = div_table.sort_values(by="Pay Date", ascending=False)
        div_table["Amount"] = div_table["Amount"].apply(lambda x: f"${x:,.2f}")

        div_table.reset_index(drop=True, inplace=True)

    if ticker.info.get('exDividendDate') is not None:
        ex_dividend_date = ticker.info.get('exDividendDate')
        dt = datetime.fromtimestamp(ex_dividend_date)
        ex_dividend_date = dt.date()

    if ticker.info.get('dividendDate') is not None:
        dividend_pay_date = ticker.info.get('dividendDate')
        dt = datetime.fromtimestamp(dividend_pay_date)
        dividend_pay_date = dt.date()

    dividend_yield = round(ticker.info.get('dividendYield', 0), 2) 

    if ticker.info.get('lastFiscalYearEnd') is not None:
        filing_date = ticker.info.get("lastFiscalYearEnd")  # or 'mostRecentQuarter'
        dt = datetime.fromtimestamp(filing_date)
        filing_date = dt.date()

    income_stmt = ticker.financials
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow

    if len(income_stmt) > 0:
        revenue = income_stmt.loc["Total Revenue"].iloc[0]
        net_income = income_stmt.loc["Net Income"].iloc[0]
    
    if ticker.info.get("trailingPE") is not None:
        pe_ratio = ticker.info.get("trailingPE")
    
    if ticker.info.get("trailingEps") is not None:
        eps = ticker.info.get("trailingEps")
    
    if ticker.info.get("revenuePerShare") is not None:
        rps = ticker.info.get("revenuePerShare")

    # To get the dates around dividends we need to use Polygon
    POLYGON_API_KEY = "Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8"

    client = RESTClient("Gby2JUpAVNhvfGbWR29CjzqqIpsRCdN8")

    dividends = client.list_dividends(ticker=symbol)

    # Convert results to DataFrame
    div_list = [div.__dict__ for div in dividends]

    # Create DataFrame
    dividend_table = pd.DataFrame(div_list)

    if len(dividend_table) > 0:    
        # Keep and rename relevant columns
        dividend_table = dividend_table[[
        "ticker",
        "declaration_date",
        "ex_dividend_date",
        "record_date",
        "pay_date",
        "cash_amount",
        "frequency"
        ]]

        dividend_table.columns = [
        "Ticker",
        "Declaration Date",
        "Ex-Dividend Date",
        "Record Date",
        "Pay Date",
        "Cash Amount",
        "Frequency"
        ]

        # Format dates
        for col in ["Declaration Date", "Ex-Dividend Date", "Record Date", "Pay Date"]:
            dividend_table[col] = pd.to_datetime(dividend_table[col]).dt.date

        # Sort by Ex-Dividend Date
        dividend_table = dividend_table.sort_values("Ex-Dividend Date", ascending=False)

        dividend_table.reset_index(drop=True, inplace=True)

    table_1_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
     }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
            color:#000;
        }

        div.st-key-colored-background,div.st-key-colored-background-2,div.st-key-colored-background-3,div.st-key-colored-background-4,div.st-key-colored-background-5,div.st-key-colored-background-6,div.st-key-colored-background-7 ,div.st-key-colored-background-8,div.st-key-colored-background-9   {
            background-color: #f0f0f0;  /* light grey background */
            border-radius: 15px;
            padding:20px
        }

        div.st-key-colored-background > div,div.st-key-colored-background-2,div.st-key-colored-background-3 > div,div.st-key-colored-background-4 > div,div.st-key-colored-background-5 > div,div.st-key-colored-background-6 > div,div.st-key-colored-background-7 > div,div.st-key-colored-background-8 > div,div.st-key-colored-background-9 > div  {
            width:95%;
        }
    </style>

    <table>
        <tr>
            <td><strong>Yesterday Open<strong></td>
            <td>""" + format_currency(yesterday_open) + """</td>
        </tr>
        </tr>
        <tr>
            <td><strong>Yesterday Close<strong></td>
            <td>""" + format_currency(yesterday_close) + """</td>
        </tr>
        <tr>
            <td><strong>Yesterday High<strong></td>
            <td>""" + format_currency(yesterday_high) + """</td>
        </tr>
        <tr>
            <td><strong>Yesterday Low<strong></td>
            <td>""" + format_currency(yesterday_low) + """</td>
    </table>
    """

    table_2_html_code = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            border: 1px solid white;
            margin-bottom:25px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        tr:nth-child(even) {
            background-color: #f0f0f0;  /* Light gray for alternate rows */
        }
    </style>

    <table>
        <tr>
            <td><strong>Volume<strong></td>
            <td>""" + "{:,}".format(int(yesterday_volume)) + """</td>
        </tr>
        <tr>
            <td><strong>Div Yield (%)<strong></td>
            <td>""" + str(dividend_yield) + """</td>
        </tr>
        <tr>
            <td><strong>Year High<strong></td>
            <td>""" + format_currency(year_high) + """</td>
        </tr>
        <tr>
            <td><strong>Year Low<strong></td>
            <td>""" + format_currency(year_low) + """</td>
        </tr>
    </table>
    """

    with st.container(key='colored-background'):
        # Set up the top column with company details
        col1, col2 = st.columns([1,9])

        with col1:
            st.write(" ")
#        st.write(get_company_logo_url("AAPL"))
#        try:
#            if(details.branding.icon_url):
#                st.image(details.branding.icon_url + '?apiKey=' + POLYGON_API_KEY, width=100)
#        except Exception as e:
#            st.write(" ")
        with col2:
            st.header(stock_name)
            st.markdown("**Symbol:** " + symbol)
        
        
        # Set up the middle columns with financials
        col11, col13, col14, col15 = st.columns(4)
        with col11:
            st.markdown(f"**Last Traded Price:**")
            st.markdown(f'<p style="font-size:28px">{format_currency(current_price)} </p>', unsafe_allow_html=True)
        with col13:
            st.markdown("**Yesterday Price Change:** ")
            if yesterday_change >= 0:
                st.markdown(f'<p style="font-size:28px;color:green">{format_currency(yesterday_change)} ({yesterday_change_pct:.2f}%)</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="font-size:28px;color:red">{format_currency(yesterday_change)} ({yesterday_change_pct:.2f}%)</p>', unsafe_allow_html=True)

        with col14:
            st.markdown(table_1_html_code, unsafe_allow_html=True)
        with col15:
            st.markdown(table_2_html_code, unsafe_allow_html=True)

        if minimal is True:
            # Set up the tabs
            tab1, tab3, tab4  = st.tabs(["Overview", "Dividend", "Chart"])

            table_3_html_code = """
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                    border: 1px solid white;
                    margin-bottom:25px;
                }
                th, td {
                    padding: 10px;
                   text-align: left;
               }
                tr:nth-child(even) {
                    background-color: #f0f0f0;  /* Light gray for alternate rows */
                }
            </style>

            <table>
                <tr>
                    <td><strong>Dividend<strong></td>
                    <td>""" + format_currency(dividend) + """</td>
                </tr>
                <tr>
                    <td><strong>Ex-dividend date<strong></td>
                    <td>""" + str(ex_dividend_date) + """</td>
               </tr>
                <tr>
                    <td><strong>Pay date<strong></td>
                    <td>""" + str(dividend_pay_date) + """</td>
               </tr>
                <tr>
                    <td><strong>Dividend yield (%)<strong></td>
                    <td>""" + str(round(dividend_yield, 2)) + """</td>
                </tr>
            </table>
            """

            table_4_html_code = """
            <style>
                table {
                    width: 100%;
                    border-collapse: collapse;
                    border: 1px solid white;
                    margin-bottom:25px;
                }
                th, td {
                    padding: 10px;
                    text-align: left;
                }
                tr:nth-child(even) {
                    background-color: #f0f0f0;  /* Light gray for alternate rows */
                }
            </style>

            <table>
                <tr>
                    <td><strong>Filing Date<strong></td>
                    <td>""" + str(filing_date) + """</td>
                </tr>
                <tr>
                    <td><strong>Revenue<strong></td>
                    <td>""" + format_currency(revenue) + """</td>
                </tr>
                <tr>
                    <td><strong>Net Income<strong></td>
                    <td>""" + format_currency(net_income) + """</td>
                </tr>
                <tr>
                    <td><strong>PE Ratio<strong></td>
                    <td>""" + str(pe_ratio) + """</td>
                </tr>
                <tr>
                    <td><strong>Earnings per Share<strong></td>
                    <td>""" + format_currency(eps) + """</td>
                </tr>
                <tr>
                    <td><strong>Revenue per Share<strong></td>
                    <td>""" + format_currency(rps) + """</td>
                </tr>
            </table>
            """

            with tab1:
                st.subheader('Last Financials')

                st.markdown(table_4_html_code, unsafe_allow_html=True)

            with tab3:

                if not symbol.strip():
                    st.error("Please select a symbol")
                else:
                    try:
                        st.subheader('Latest Dividend Information')

                        st.markdown(table_3_html_code, unsafe_allow_html=True)

                        st.subheader("Dividend History")
                        st.dataframe(dividend_table, hide_index=True)

                    except Exception as e:
                        st.exception(f"Exception: {e}")
        
            with tab4:
                if not symbol.strip():
                    st.error("Please select a symbol")
                else:
                    st.subheader("Price History")
                
                    # Get the list of events
                    events_df = pd.read_csv("data/us_holidays_events_20yrs.csv")
                    events_df["Date"] = pd.to_datetime(events_df["Date"])

                    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
                    end_date = st.date_input("End Date", pd.to_datetime("today"))

                    if ticker:
                        # Load historical data
                        hist = ticker.history(start=start_date, end=end_date)

                        if not hist.empty:
                        # Create Plotly figure
                            fig = go.Figure()

                            # Line for Close price
                            fig.add_trace(go.Scatter(
                                x=hist.index,
                                y=hist["Close"],
                                mode="lines",
                                name="Close Price"
                            ))

                            # Strip timezone from hist.index
                            hist.index = hist.index.tz_localize(None)

                            # Filter holidays to match chart range
                            holiday_events = events_df[
                            (events_df["Date"] >= hist.index.min()) &
                                (events_df["Date"] <= hist.index.max())
                            ]

                        # Add annotations for each holiday
                            for _, row in holiday_events.iterrows():
                                event_date = row["Date"]
                                label = f"{row['Icon']}" if row["Icon"] else row["Event"]

                                # Find nearest date in stock data
                                closest_idx = hist.index.get_indexer([event_date], method='nearest')[0]
                                plot_date = hist.index[closest_idx]
                                price = hist["Close"].iloc[closest_idx]

                                fig.add_annotation(
                                    x=plot_date,
                                    y=price,
                                    text=label,
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-40
                                )

                        #dividend_table
                        # Filter dividends to match chart range
                        if len(dividend_table) > 0:
                            dividend_table["Pay Date"] = pd.to_datetime(dividend_table["Pay Date"])
                            dividend_table = dividend_table[
                            (dividend_table["Pay Date"] >= hist.index.min()) &
                                (dividend_table["Pay Date"] <= hist.index.max())
                            ]

                            for _, row in dividend_table.iterrows():
                                declaration_date = row["Declaration Date"]
                                ex_date = row["Ex-Dividend Date"]
                                pay_date = row["Pay Date"]
                                price = 0
                            
                                # Find closest trading day in data
                                if declaration_date in hist.index:
                                    price = hist.loc[declaration_date, "Close"]
                                else:
                                    closest_idx = hist.index.get_indexer([declaration_date], method='nearest')[0]
                                    declaration_date = hist.index[closest_idx]
                                    price = hist["Close"].iloc[closest_idx]

                                fig.add_annotation(
                                    x=declaration_date,
                                    y=price,
                                    text="📣",  # or use "📤", "💰", etc.
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-40
                                )
                            
                                # Find closest trading day in data
                                if ex_date in hist.index:
                                    price = hist.loc[ex_date, "Close"]
                                else:
                                    closest_idx = hist.index.get_indexer([ex_date], method='nearest')[0]
                                    ex_date = hist.index[closest_idx]
                                    price = hist["Close"].iloc[closest_idx]

                                fig.add_annotation(
                                    x=ex_date,
                                    y=price,
                                    text="⚠️",  # or use "📤", "💰", etc.
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-40
                                )
                            
                                # Find closest trading day in data
                                if pay_date in hist.index:
                                    price = hist.loc[pay_date, "Close"]
                                else:
                                    closest_idx = hist.index.get_indexer([pay_date], method='nearest')[0]
                                    pay_date = hist.index[closest_idx]
                                    price = hist["Close"].iloc[closest_idx]

                                fig.add_annotation(
                                    x=pay_date,
                                    y=price,
                                    text="💰",  # or use "📤", "💰", etc.
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-40
                                )

                        # Layout
                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Price (USD)",
                            hovermode="x"
                        )

                        # Show chart
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No data found for this ticker and date range.")


def get_company_logo_url(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info

    website = info.get('website')
    if website:
        # Extract domain name
         domain = website.replace("http://", "").replace("https://", "").split("/")[0]
         logo_url = f"https://logo.clearbit.com/{domain}"
         return logo_url
    return None
    

@st.cache_data
def load_symbols():
    symbols = pd.read_csv("data/nasdaqlisted.csv", sep='|')
    return symbols 

def format_currency(value, symbol="$"):
    return f"{symbol}{value:,.2f}"
