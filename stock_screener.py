import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with RSI Integration
st.title("Indian Stock Screening Tool with RSI Integration")
st.write("""
### Analyze daily, weekly, and monthly buy, exit, and stop-loss levels using RSI.
""")

# Sidebar for User Input
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

# Function to Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        
        # Calculate Technical Indicators
        data["RSI"] = calculate_rsi(data)
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        # Timeframe-Specific Calculations
        def levels_for_timeframe(data, period):
            data_period = data[-period:]
            buy = data_period["Lower_BB"].mean()
            exit = data_period["Upper_BB"].mean()
            stop_loss = buy * 0.97
            avg_rsi = data_period["RSI"].mean()
            return buy, exit, stop_loss, avg_rsi

        # Daily, Weekly, Monthly Levels
        daily_buy, daily_exit, daily_stop_loss, daily_rsi = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss, weekly_rsi = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss, monthly_rsi = levels_for_timeframe(data, 20)

        return {
            "Ticker": ticker,
            "Daily Buy Price": round(daily_buy, 2),
            "Daily Exit Price": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2),
            "Daily RSI": round(daily_rsi, 2),
            "Weekly Buy Price": round(weekly_buy, 2),
            "Weekly Exit Price": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2),
            "Weekly RSI": round(weekly_rsi, 2),
            "Monthly Buy Price": round(monthly_buy, 2),
            "Monthly Exit Price": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2),
            "Monthly RSI": round(monthly_rsi, 2),
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
st.header("Stock Screening Results with RSI Integration")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")
