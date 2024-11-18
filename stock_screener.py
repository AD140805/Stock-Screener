import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with Multi-Timeframe Levels
st.title("Indian Stock Screening Tool with Multi-Timeframe Levels")
st.write("""
### Analyze daily, weekly, and monthly buy, exit, and stop-loss levels for Indian stocks.
""")

# Sidebar for User Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# Function to Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        
        # Calculate Technical Indicators
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        # Timeframe-Specific Calculations
        # Daily
        daily_buy = data["Lower_BB"][-1]
        daily_exit = data["Upper_BB"][-1]
        daily_stop_loss = daily_buy * 0.97

        # Weekly (5-Day Rolling Average)
        weekly_data = data[-5:]
        weekly_buy = weekly_data["Lower_BB"].mean()
        weekly_exit = weekly_data["Upper_BB"].mean()
        weekly_stop_loss = weekly_buy * 0.97

        # Monthly (20-Day Rolling Average)
        monthly_data = data[-20:]
        monthly_buy = monthly_data["Lower_BB"].mean()
        monthly_exit = monthly_data["Upper_BB"].mean()
        monthly_stop_loss = monthly_buy * 0.97

        return {
            "Ticker": ticker,
            "Daily Buy Price": round(daily_buy, 2),
            "Daily Exit Price": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2),
            "Weekly Buy Price": round(weekly_buy, 2),
            "Weekly Exit Price": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2),
            "Monthly Buy Price": round(monthly_buy, 2),
            "Monthly Exit Price": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2),
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
st.header("Stock Screening Results with Multi-Timeframe Levels")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

