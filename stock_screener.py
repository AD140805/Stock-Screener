import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Advanced Stock Screener", page_icon="📈", layout="wide")

# App Title
st.title("📊 Advanced Indian Stock Screener")
st.markdown("""
Analyze Indian stocks with dynamic buy/sell ranges, advanced indicators, support/resistance levels, and customizable charts!
""")

# Sidebar Input for Stock Selection
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")
tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]

# Indicator Selection
indicators = st.sidebar.multiselect(
    "Select Indicators to Display",
    options=["RSI", "ATR", "EMA (50)", "EMA (200)", "Bollinger Bands", "Support/Resistance"],
    default=["RSI", "ATR", "EMA (50)", "Bollinger Bands"]
)

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

# Support/Resistance Calculation
def calculate_support_resistance(data):
    supports = []
    resistances = []
    for i in range(2, len(data) - 2):
        if data['Low'][i] < data['Low'][i-1] and data['Low'][i] < data['Low'][i+1]:
            supports.append({'level': data['Low'][i], 'type': 'support'})
        if data['High'][i] > data['High'][i-1] and data['High'][i] > data['High'][i+1]:
            resistances.append({'level': data['High'][i], 'type': 'resistance'})
    return supports, resistances

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
        data["Upper_BB"] = data['Close'].rolling(window=20).mean() + 2 * data['Close'].rolling(window=20).std()
        data["Lower_BB"] = data['Close'].rolling(window=20).mean() - 2 * data['Close'].rolling(window=20).std()

        # Calculate Dynamic Ranges
        def calculate_ranges(data_period):
            if data_period.empty:
                return None, None, None
            buy = data_period["Lower_BB"].mean()
            sell = data_period["Upper_BB"].mean()
            atr = data_period["ATR"].mean()
            return (round(buy - atr, 2), round(buy + atr, 2)), (round(sell - atr, 2), round(sell + atr, 2)), round(buy - (2 * atr), 2)

        daily_data = data[-1:]
        daily_buy, daily_sell, daily_stop_loss = calculate_ranges(daily_data)

        # Support/Resistance Levels
        supports, resistances = calculate_support_resistance(data)

        return {
            "Ticker": ticker,
            "Data": data,
            "Daily Buy Range": daily_buy,
            "Daily Sell Range": daily_sell,
            "Daily Stop Loss": daily_stop_loss,
            "Support Levels": supports,
            "Resistance Levels": resistances
        }
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

    # Add Selected Indicators
    if "RSI" in indicators:
        st.write(f"RSI: {round(data['RSI'].iloc[-1], 2)}")
    if "ATR" in indicators:
        st.write(f"ATR: {round(data['ATR'].iloc[-1], 2)}")
    if "EMA (50)" in indicators:
        fig.add_trace(go.Scatter(
            x=data.index, y=data["EMA_50"], mode='lines',
            name="50-Day EMA", line=dict(color="blue", dash='dot')
        ))
    if "EMA (200)" in indicators:
        fig.add_trace(go.Scatter(
            x=data.index, y=data["EMA_200"], mode='lines',
            name="200-Day EMA", line=dict(color="purple", dash='dash')
        ))
    if "Bollinger Bands" in indicators:
        fig.add_trace(go.Scatter(
            x=data.index, y=data["Upper_BB"], mode='lines',
            name="Upper Bollinger Band", line=dict(color="green")
        ))
        fig.add_trace(go.Scatter(
            x=data.index, y=data["Lower_BB"], mode='lines',
            name="Lower Bollinger Band", line=dict(color="green")
        ))

    # Add Support/Resistance Levels
    if "Support/Resistance" in indicators:
        supports = result["Support Levels"]
        resistances = result["Resistance Levels"]
        for s in supports:
            fig.add_hline(y=s['level'], line_dash="dot", line_color="green")
        for r in resistances:
            fig.add_hline(y=r['level'], line_dash="dot", line_color="red")

    # Chart Layout
    fig.update_layout(
        title=f"Technical Chart for {ticker}",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=600
    )
    st.plotly_chart(fig)

    # Display Ranges
    st.markdown(f"### Daily Buy/Sell/Stop Loss Ranges for {ticker}")
    st.write(f"**Buy Range:** {result['Daily Buy Range']}")
    st.write(f"**Sell Range:** {result['Daily Sell Range']}")
    st.write(f"**Stop Loss:** {result['Daily Stop Loss']}")
