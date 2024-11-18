import yfinance as yf
import pandas as pd
import streamlit as st

# Web App: Indian Stock Screener

# Title and Introduction
st.title("Indian Stock Screening Tool")
st.write("""
### A simple stock screener for the Indian equity market.
This tool ranks stocks based on key fundamental and technical metrics.
""")

# Sidebar for User Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# Function to Fetch and Process Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="1y")
        info = stock.info

        # Calculate Technical Indicators
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        rsi = 100 - (100 / (1 + data["Close"].pct_change().mean()))

        # Fundamental Metrics
        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        roe = info.get("returnOnEquity", None) * 100 if info.get("returnOnEquity") else None
        debt_to_equity = info.get("debtToEquity", None)
        market_cap = info.get("marketCap", None)

        # Scoring
        score = 0
        if pe_ratio and pe_ratio < 25: score += 10  # Favor low P/E
        if pb_ratio and pb_ratio < 3: score += 10  # Favor low P/B
        if roe and roe > 15: score += 20  # Favor high ROE
        if debt_to_equity and debt_to_equity < 1: score += 10  # Favor low debt
        if data["Close"][-1] > data["50_MA"][-1]: score += 10  # Technical strength

        return {
            "Ticker": ticker,
            "P/E": pe_ratio,
            "P/B": pb_ratio,
            "ROE (%)": roe,
            "D/E": debt_to_equity,
            "Market Cap (₹ Cr)": market_cap / 1e7 if market_cap else None,
            "Score": score
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Convert Results to DataFrame
df = pd.DataFrame(results)

# Display Results
st.header("Stock Screening Results")
if not df.empty:
    st.dataframe(df.sort_values(by="Score", ascending=False))
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")
else:
    st.write("No valid data to display. Please check the stock tickers entered.")
