import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit Config
st.set_page_config(page_title="Enhanced Stock Screener", page_icon="📈", layout="wide")

# Title
st.title("📊 Enhanced Indian Stock Screening Tool")
st.markdown("""
Analyze **daily**, **weekly**, and **monthly** buy, exit, and stop-loss levels with additional parameters like **MACD**, **Volume Trends**, and **ATR**.
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

def calculate_macd(data):
    ema_12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = data["Close"].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

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
        
        # Calculate Indicators
        data["RSI"] = calculate_rsi(data)
        data["MACD"], data["Signal_Line"] = calculate_macd(data)
        data["ATR"] = calculate_atr(data)
        data["Upper_BB"], data["Lower_BB"] = calculate_bollinger_bands(data)

        # Timeframe Levels
        def levels_for_timeframe(data, period):
            data_period = data[-period:]
            buy = data_period["Lower_BB"].mean()
            exit = data_period["Upper_BB"].mean()
            stop_loss = buy - data_period["ATR"].mean()
            avg_rsi = data_period["RSI"].mean()
            return buy, exit, stop_loss, avg_rsi

        daily_buy, daily_exit, daily_stop_loss, daily_rsi = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss, weekly_rsi = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss, monthly_rsi = levels_for_timeframe(data, 20)

        return {
            "Ticker": ticker,
            "Daily Buy": round(daily_buy, 2),
            "Daily Exit": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2),
            "Daily RSI": round(daily_rsi, 2),
            "Weekly Buy": round(weekly_buy, 2),
            "Weekly Exit": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2),
            "Weekly RSI": round(weekly_rsi, 2),
            "Monthly Buy": round(monthly_buy, 2),
            "Monthly Exit": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2),
            "Monthly RSI": round(monthly_rsi, 2),
            "MACD": data["MACD"].iloc[-1],
            "Signal Line": data["Signal_Line"].iloc[-1],
            "ATR": data["ATR"].iloc[-1],
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
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name="Close Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Upper_BB"], mode='lines', name="Upper Bollinger Band"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Lower_BB"], mode='lines', name="Lower Bollinger Band"))
    fig.update_layout(title=f"Technical Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)
