import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Enhanced Stock Screener", page_icon="📈", layout="wide")

# App Title
st.title("📊 Advanced Indian Stock Screening Tool")
st.markdown("""
Analyze Indian stocks with dynamic buy/sell ranges, advanced indicators, fundamental insights, and more!
""")

# Sidebar Input for Stock Selection
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")
tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]

# Toggle to Include Fibonacci Retracement
include_fibonacci = st.sidebar.checkbox("Include Fibonacci Retracement Levels", value=True)

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

# EMA Calculation Function
def calculate_ema(data, period=50):
    return data['Close'].ewm(span=period, adjust=False).mean()

# Fetch and Analyze Stock Data
@st.cache_data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="1y")
        if data.empty:
            return {"Ticker": ticker, "Error": "No data available"}

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data).fillna(50)
        data["ATR"] = calculate_atr(data).fillna(method='bfill')
        data["EMA_50"] = calculate_ema(data, period=50)
        data["EMA_200"] = calculate_ema(data, period=200)
        data["50_MA"] = data['Close'].rolling(window=50).mean()
        data["200_MA"] = data['Close'].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        return {"Ticker": ticker, "Data": data}
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Display Results
st.header("📋 Stock Screening Results")
for result in results:
    if "Error" in result:
        st.warning(f"Error fetching data for {result['Ticker']}: {result['Error']}")
        continue

    ticker = result['Ticker']
    data = result['Data']

    st.subheader(f"📈 {ticker} Technical Chart")

    # Plot Technical Chart
    fig = go.Figure()

    # Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candlestick'
    ))

    # Moving Averages
    fig.add_trace(go.Scatter(
        x=data.index, y=data['50_MA'],
        mode='lines', name="50-Day MA",
        line=dict(color="orange", dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=data['200_MA'],
        mode='lines', name="200-Day MA",
        line=dict(color="red", dash='dot')
    ))

    # Exponential Moving Averages
    fig.add_trace(go.Scatter(
        x=data.index, y=data['EMA_50'],
        mode='lines', name="50-Day EMA",
        line=dict(color="blue", dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=data['EMA_200'],
        mode='lines', name="200-Day EMA",
        line=dict(color="purple", dash='dash')
    ))

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=data.index, y=data["Upper_BB"], mode='lines',
        name="Upper Bollinger Band", line=dict(width=1, color="green")
    ))
    fig.add_trace(go.Scatter(
        x=data.index, y=data["Lower_BB"], mode='lines',
        name="Lower Bollinger Band", line=dict(width=1, color="green")
    ))

    # Fibonacci Retracement
    if include_fibonacci:
        high = data['High'].max()
        low = data['Low'].min()
        diff = high - low
        levels = [high - diff * ratio for ratio in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]]
        for level in levels:
            fig.add_hline(y=level, line_dash="dash", line_color="gold", opacity=0.5)

    # Chart Layout
    fig.update_layout(
        title=f"Technical Chart for {ticker}",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=600
    )
    st.plotly_chart(fig)

    # Display Key Metrics
    st.markdown(f"### Key Metrics for {ticker}")
    metrics = {
        "RSI": round(data["RSI"].iloc[-1], 2),
        "ATR": round(data["ATR"].iloc[-1], 2),
        "50-Day EMA": round(data["EMA_50"].iloc[-1], 2),
        "200-Day EMA": round(data["EMA_200"].iloc[-1], 2),
        "Latest Close Price": round(data["Close"].iloc[-1], 2),
    }
    st.table(pd.DataFrame.from_dict(metrics, orient="index", columns=["Value"]))

# Footer Branding
st.markdown("""
    <div style="text-align: center; margin-top: 30px; color: #888;">
        Built with ❤️ using <b>Streamlit</b> | Inspired by <b>TradingView</b>
    </div>
""", unsafe_allow_html=True)
