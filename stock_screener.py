import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with Enhanced Technical Indicators
st.title("Indian Stock Screening Tool with Enhanced Technical Analysis")
st.write("""
### Analyze buy, exit, and stop-loss levels with MACD, Volume, and ATR.
""")

# Sidebar for User Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# MACD Calculation
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data['Close'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['Close'].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

# ATR Calculation
def calculate_atr(data, period=14):
    data['High-Low'] = data['High'] - data['Low']
    data['High-Close'] = abs(data['High'] - data['Close'].shift())
    data['Low-Close'] = abs(data['Low'] - data['Close'].shift())
    true_range = data[['High-Low', 'High-Close', 'Low-Close']].max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

# Function to Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        
        # Calculate Indicators
        macd, signal = calculate_macd(data)
        atr = calculate_atr(data)
        data["MACD"] = macd
        data["Signal"] = signal
        data["ATR"] = atr
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        # Signals
        buy_signal = data.iloc[-1]["Lower_BB"] if data.iloc[-1]["MACD"] > data.iloc[-1]["Signal"] else None
        exit_signal = data.iloc[-1]["Upper_BB"] if data.iloc[-1]["MACD"] < data.iloc[-1]["Signal"] else None
        stop_loss = buy_signal - (1.5 * data.iloc[-1]["ATR"]) if buy_signal else None

        return {
            "Ticker": ticker,
            "Buy Price": round(buy_signal, 2) if buy_signal else None,
            "Exit Price": round(exit_signal, 2) if exit_signal else None,
            "Stop Loss": round(stop_loss, 2) if stop_loss else None,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Convert Results to DataFrame
summary = [
    {k: v for k, v in res.items()} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)

# Display Results
st.header("Stock Screening Results with Enhanced Technical Analysis")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")
