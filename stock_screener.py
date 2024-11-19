import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Advanced Stock Screener", page_icon="📈", layout="wide")

# App Title
st.title("📊 Advanced Indian Stock Screening Tool")
st.markdown("""
Get **dynamic buy/sell ranges**, **advanced indicators**, and **fundamental analysis** for Indian stocks. 
""")

# Sidebar for Stock Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# RSI Calculation Function
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ATR Calculation Function
def calculate_atr(data, period=14):
    high_low = data['High'] - data['Low']
    high_close = abs(data['High'] - data['Close'].shift())
    low_close = abs(data['Low'] - data['Close'].shift())
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()

# MACD Calculation Function
def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    short_ema = data['Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line, signal_line

# Fetch and Analyze Stock Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")

        if len(data) < 20:
            return {"Ticker": ticker, "Error": "Not enough data to calculate indicators"}
        
        # Calculate Indicators
        data["RSI"] = calculate_rsi(data).fillna(50)
        data["ATR"] = calculate_atr(data).fillna(method='bfill')
        data["50_MA"] = data["Close"].rolling(window=50).mean().fillna(method='bfill')
        data["200_MA"] = data["Close"].rolling(window=200).mean().fillna(method='bfill')
        data["Upper_BB"] = (data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()).fillna(method='bfill')
        data["Lower_BB"] = (data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()).fillna(method='bfill')
        data["MACD_Line"], data["Signal_Line"] = calculate_macd(data)

        # Calculate Dynamic Ranges
        def calculate_ranges(data_period):
            if data_period.empty:
                return None, None, None
            buy = data_period["Lower_BB"].mean()
            sell = data_period["Upper_BB"].mean()
            atr = data_period["ATR"].mean()
            return (buy - atr, buy + atr), (sell - atr, sell + atr), buy - (2 * atr)

        daily_data = data[-1:]
        weekly_data = data[-5:]
        monthly_data = data[-20:]

        daily_buy, daily_sell, daily_stop_loss = calculate_ranges(daily_data)
        weekly_buy, weekly_sell, weekly_stop_loss = calculate_ranges(weekly_data)
        monthly_buy, monthly_sell, monthly_stop_loss = calculate_ranges(monthly_data)

        return {
            "Ticker": ticker,
            "Daily Buy Range": daily_buy,
            "Daily Sell Range": daily_sell,
            "Daily Stop Loss": daily_stop_loss,
            "Weekly Buy Range": weekly_buy,
            "Weekly Sell Range": weekly_sell,
            "Weekly Stop Loss": weekly_stop_loss,
            "Monthly Buy Range": monthly_buy,
            "Monthly Sell Range": monthly_sell,
            "Monthly Stop Loss": monthly_stop_loss,
            "RSI": round(data["RSI"].iloc[-1], 2),
            "MACD Line": round(data["MACD_Line"].iloc[-1], 2),
            "Signal Line": round(data["Signal_Line"].iloc[-1], 2),
            "ATR": round(data["ATR"].iloc[-1], 2),
            "Data": data
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Display Results
summary = [
    {k: v for k, v in res.items() if k != "Data"} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)

st.header("📋 Stock Screening Results")
if not df.empty:
    st.dataframe(df)
    st.download_button("📥 Download All Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Chart Display
st.header("📊 Technical Charts")
for res in results:
    if "Error" in res:
        st.warning(f"Error fetching data for {res['Ticker']}: {res['Error']}")
        continue

    data = res["Data"]
    ticker = res["Ticker"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name="Close Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data["50_MA"], mode='lines', name="50-Day MA"))
    fig.add_trace(go.Scatter(x=data.index, y=data["200_MA"], mode='lines', name="200-Day MA"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Upper_BB"], mode='lines', name="Upper Bollinger Band"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Lower_BB"], mode='lines', name="Lower Bollinger Band"))
    fig.add_trace(go.Bar(x=data.index, y=data["Volume"], name="Volume", opacity=0.3))

    fig.update_layout(title=f"Technical Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)

# Fundamental Analysis Placeholder
st.sidebar.header("Fundamental Analysis")
for ticker in tickers:
    stock = yf.Ticker(ticker.strip())
    info = stock.info
    st.sidebar.subheader(f"{ticker} Fundamentals")
    st.sidebar.write(f"Market Cap: {info.get('marketCap')}")
    st.sidebar.write(f"PE Ratio: {info.get('trailingPE')}")
    st.sidebar.write(f"EPS: {info.get('trailingEps')}")
    st.sidebar.write(f"Dividend Yield: {info.get('dividendYield')}")
