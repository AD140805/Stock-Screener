import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit Config
st.set_page_config(page_title="Stock Screener", page_icon="📈", layout="wide")

# Title
st.title("📊 Indian Stock Screening Tool")
st.markdown("""
Get **daily**, **weekly**, and **monthly** buy, exit, and stop-loss levels for Indian stocks using **RSI**, **ATR**, and Bollinger Bands.
""")

# Sidebar Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# Indicator Functions
def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(data, period=14):
    high_low = data["High"] - data["Low"]
    high_close = abs(data["High"] - data["Close"].shift())
    low_close = abs(data["Low"] - data["Close"].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

def calculate_bollinger_bands(data, window=20):
    rolling_mean = data["Close"].rolling(window=window).mean()
    rolling_std = data["Close"].rolling(window=window).std()
    upper_band = rolling_mean + 2 * rolling_std
    lower_band = rolling_mean - 2 * rolling_std
    return upper_band, lower_band

# Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")

        if len(data) < 20:
            return {"Ticker": ticker, "Error": "Not enough data to compute indicators"}

        # Calculate Daily Indicators
        data["RSI"] = calculate_rsi(data)
        data["ATR"] = calculate_atr(data)
        data["Upper_BB"], data["Lower_BB"] = calculate_bollinger_bands(data)

        # Resample Data for Weekly and Monthly
        data_weekly = data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        data_monthly = data.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # Recalculate Indicators for Weekly and Monthly
        data_weekly["RSI"] = calculate_rsi(data_weekly)
        data_weekly["ATR"] = calculate_atr(data_weekly)
        data_weekly["Upper_BB"], data_weekly["Lower_BB"] = calculate_bollinger_bands(data_weekly)

        data_monthly["RSI"] = calculate_rsi(data_monthly)
        data_monthly["ATR"] = calculate_atr(data_monthly)
        data_monthly["Upper_BB"], data_monthly["Lower_BB"] = calculate_bollinger_bands(data_monthly)

        # Level Calculation Function
        def calculate_levels(data_period):
            if len(data_period) < 1 or data_period.isnull().values.any():
                return None, None, None

            lower_bb = data_period["Lower_BB"].iloc[-1]
            rsi = data_period["RSI"].iloc[-1]
            buy_price = lower_bb if rsi < 30 else data_period["Close"].iloc[-1]

            upper_bb = data_period["Upper_BB"].iloc[-1]
            exit_price = upper_bb if rsi > 70 else data_period["Close"].iloc[-1]

            atr = data_period["ATR"].iloc[-1]
            stop_loss = buy_price - atr if buy_price and atr else None

            return buy_price, exit_price, stop_loss

        # Calculate Levels for Each Timeframe
        daily_buy, daily_exit, daily_stop_loss = calculate_levels(data[-1:])
        weekly_buy, weekly_exit, weekly_stop_loss = calculate_levels(data_weekly[-1:])
        monthly_buy, monthly_exit, monthly_stop_loss = calculate_levels(data_monthly[-1:])

        # Debug Outputs for Validation
        st.write(f"Debugging {ticker}:")
        st.write("Daily Data Sample", data.tail())
        st.write("Weekly Data Sample", data_weekly.tail())
        st.write("Monthly Data Sample", data_monthly.tail())

        return {
            "Ticker": ticker,
            "Daily Buy": round(daily_buy, 2) if daily_buy else "N/A",
            "Daily Exit": round(daily_exit, 2) if daily_exit else "N/A",
            "Daily Stop Loss": round(daily_stop_loss, 2) if daily_stop_loss else "N/A",
            "Weekly Buy": round(weekly_buy, 2) if weekly_buy else "N/A",
            "Weekly Exit": round(weekly_exit, 2) if weekly_exit else "N/A",
            "Weekly Stop Loss": round(weekly_stop_loss, 2) if weekly_stop_loss else "N/A",
            "Monthly Buy": round(monthly_buy, 2) if monthly_buy else "N/A",
            "Monthly Exit": round(monthly_exit, 2) if monthly_exit else "N/A",
            "Monthly Stop Loss": round(monthly_stop_loss, 2) if monthly_stop_loss else "N/A",
            "Data": data
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Process All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Display Results
st.header("📋 Stock Screening Results")
summary = [
    {k: v for k, v in res.items() if k != "Data"} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)
if not df.empty:
    st.dataframe(df)
else:
    st.warning("No valid data to display. Please check the tickers or try again.")

# Plot Charts
st.header("📊 Technical Charts")
for res in results:
    if "Error" in res:
        st.warning(f"Error fetching data for {res['Ticker']}: {res['Error']}")
        continue

    data = res["Data"]
    ticker = res["Ticker"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Close Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Upper_BB"], mode="lines", name="Upper Bollinger Band"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Lower_BB"], mode="lines", name="Lower Bollinger Band"))
    fig.update_layout(title=f"Technical Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)
