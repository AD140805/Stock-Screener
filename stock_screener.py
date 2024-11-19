import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit Config
st.set_page_config(page_title="Advanced Stock Screener", page_icon="📈", layout="wide")

# Title
st.title("📊 Enhanced Indian Stock Screening Tool")
st.markdown("""
Analyze **daily**, **weekly**, and **monthly** buy, exit, and stop-loss levels for Indian stocks with **RSI**, **ATR**, and more.
""")

# Sidebar Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")
tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]

# Sidebar: Indicator Selection
indicators = st.sidebar.multiselect(
    "Select Indicators to Display",
    options=["RSI", "ATR", "Bollinger Bands", "EMA (50)", "EMA (200)", "Support/Resistance"],
    default=["RSI", "ATR", "Bollinger Bands", "Support/Resistance"]
)

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
    return true_range.rolling(window=period).mean()

def calculate_bollinger_bands(data, window=20):
    rolling_mean = data["Close"].rolling(window=window).mean()
    rolling_std = data["Close"].rolling(window=window).std()
    upper_band = rolling_mean + 2 * rolling_std
    lower_band = rolling_mean - 2 * rolling_std
    return upper_band, lower_band

def calculate_ema(data, period=50):
    return data["Close"].ewm(span=period, adjust=False).mean()

def calculate_support_resistance(data):
    supports, resistances = [], []
    for i in range(2, len(data) - 2):
        if data["Low"][i] < data["Low"][i-1] and data["Low"][i] < data["Low"][i+1]:
            supports.append(data["Low"][i])
        if data["High"][i] > data["High"][i-1] and data["High"][i] > data["High"][i+1]:
            resistances.append(data["High"][i])
    return supports, resistances

# Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        if data.empty:
            return {"Ticker": ticker, "Error": "No data available"}

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data).fillna(50)
        data["ATR"] = calculate_atr(data).fillna(data["Close"].std())
        data["Upper_BB"], data["Lower_BB"] = calculate_bollinger_bands(data)
        data["EMA_50"] = calculate_ema(data, period=50)
        data["EMA_200"] = calculate_ema(data, period=200)

        # Timeframe Levels
        def calculate_levels(data_period):
            if len(data_period) < 1:
                return None, None, None
            lower_bb = data_period["Lower_BB"].iloc[-1]
            rsi = data_period["RSI"].iloc[-1]
            buy_price = lower_bb if rsi < 30 else data_period["Close"].iloc[-1]
            upper_bb = data_period["Upper_BB"].iloc[-1]
            exit_price = upper_bb if rsi > 70 else data_period["Close"].iloc[-1]
            atr = data_period["ATR"].iloc[-1]
            stop_loss = buy_price - atr if buy_price else None
            return buy_price, exit_price, stop_loss

        daily_buy, daily_exit, daily_stop_loss = calculate_levels(data[-1:])
        weekly_buy, weekly_exit, weekly_stop_loss = calculate_levels(data[-5:])
        monthly_buy, monthly_exit, monthly_stop_loss = calculate_levels(data[-20:])
        supports, resistances = calculate_support_resistance(data)

        return {
            "Ticker": ticker,
            "Daily Buy": round(daily_buy, 2),
            "Daily Exit": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2) if daily_stop_loss else "N/A",
            "Weekly Buy": round(weekly_buy, 2),
            "Weekly Exit": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2) if weekly_stop_loss else "N/A",
            "Monthly Buy": round(monthly_buy, 2),
            "Monthly Exit": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2) if monthly_stop_loss else "N/A",
            "Support Levels": supports,
            "Resistance Levels": resistances,
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

    # Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Candlestick"
    ))

    # Bollinger Bands
    if "Bollinger Bands" in indicators:
        fig.add_trace(go.Scatter(x=data.index, y=data["Upper_BB"], mode="lines", name="Upper BB"))
        fig.add_trace(go.Scatter(x=data.index, y=data["Lower_BB"], mode="lines", name="Lower BB"))

    # Support and Resistance Levels
    if "Support/Resistance" in indicators:
        for s in res["Support Levels"]:
            fig.add_hline(y=s, line_dash="dot", line_color="green")
        for r in res["Resistance Levels"]:
            fig.add_hline(y=r, line_dash="dot", line_color="red")

    # Chart Layout
    fig.update_layout(title=f"Technical Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)
