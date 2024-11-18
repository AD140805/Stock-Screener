import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit Config
st.set_page_config(page_title="Enhanced Stock Screener", page_icon="📈", layout="wide")

# Title
st.title("📊 Enhanced Indian Stock Screening Tool")
st.markdown("""
Analyze **daily**, **weekly**, and **monthly** buy, exit, and stop-loss levels using advanced parameters like **RSI** and **ATR**.
""")

# Sidebar
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area("Enter stock tickers (comma-separated):", value=", ".join(default_tickers)).split(",")

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
    true_range = high_low.combine(high_close, max).combine(low_close, max)
    atr = true_range.rolling(window=period).mean()
    return atr

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
        
        # Handle insufficient data
        if len(data) < 20:
            return {"Ticker": ticker, "Error": "Insufficient data for analysis"}

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data)
        data["ATR"] = calculate_atr(data)
        data["Upper_BB"], data["Lower_BB"] = calculate_bollinger_bands(data)

        # Timeframe Levels
        def levels_for_timeframe(data, period):
            data_period = data[-period:]

            # Validate data availability
            if len(data_period) < period:
                return None, None, None

            # Determine Buy Price
            lower_bb = data_period["Lower_BB"].iloc[-1]
            rsi = data_period["RSI"].iloc[-1]
            buy = lower_bb if rsi < 30 else None

            # Determine Exit Price
            upper_bb = data_period["Upper_BB"].iloc[-1]
            exit = upper_bb if rsi > 70 else None

            # Determine Stop Loss
            atr = data_period["ATR"].iloc[-1]
            stop_loss = buy - atr if buy else None

            return buy, exit, stop_loss

        daily_buy, daily_exit, daily_stop_loss = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss = levels_for_timeframe(data, 20)

        # Handle cases where levels are None
        def safe_round(value):
            return round(value, 2) if value is not None else "N/A"

        return {
            "Ticker": ticker,
            "Daily Buy": safe_round(daily_buy),
            "Daily Exit": safe_round(daily_exit),
            "Daily Stop Loss": safe_round(daily_stop_loss),
            "Weekly Buy": safe_round(weekly_buy),
            "Weekly Exit": safe_round(weekly_exit),
            "Weekly Stop Loss": safe_round(weekly_stop_loss),
            "Monthly Buy": safe_round(monthly_buy),
            "Monthly Exit": safe_round(monthly_exit),
            "Monthly Stop Loss": safe_round(monthly_stop_loss),
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
st.dataframe(df)

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
