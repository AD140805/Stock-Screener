import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with Buy/Sell Suggestions
st.title("Indian Stock Screening Tool with Buy/Sell Suggestions")
st.write("""
### Analyze fundamental and technical indicators for Indian stocks.
This tool also suggests potential buy prices, exit points, and stop loss levels.
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
        data = stock.history(period="1y")
        
        # Calculate Technical Indicators
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()
        rsi = 100 - (100 / (1 + data["Close"].pct_change().mean()))
        
        # Suggested Buy Price: Near Lower Bollinger Band or Support Level
        buy_price = data["Lower_BB"][-1]

        # Suggested Exit Price: Near Upper Bollinger Band or Resistance Level
        exit_price = data["Upper_BB"][-1]

        # Suggested Stop Loss: Slightly Below Support Level
        stop_loss = buy_price * 0.97  # 3% below buy price

        # Fundamental Metrics
        info = stock.info
        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        roe = info.get("returnOnEquity", None) * 100 if info.get("returnOnEquity") else None
        debt_to_equity = info.get("debtToEquity", None)
        market_cap = info.get("marketCap", None)

        # Scoring
        score = 0
        if pe_ratio and pe_ratio < 25: score += 10
        if pb_ratio and pb_ratio < 3: score += 10
        if roe and roe > 15: score += 20
        if debt_to_equity and debt_to_equity < 1: score += 10
        if data["Close"][-1] > data["50_MA"][-1]: score += 10

        return {
            "Ticker": ticker,
            "P/E": pe_ratio,
            "P/B": pb_ratio,
            "ROE (%)": roe,
            "D/E": debt_to_equity,
            "Market Cap (₹ Cr)": market_cap / 1e7 if market_cap else None,
            "RSI": round(rsi, 2),
            "Buy Price": round(buy_price, 2),
            "Exit Price": round(exit_price, 2),
            "Stop Loss": round(stop_loss, 2),
            "Score": score,
            "Data": data
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Convert Results to DataFrame
summary = [
    {k: v for k, v in res.items() if k not in ["Data"]} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)

# Display Results
st.header("Stock Screening Results")
if not df.empty:
    st.dataframe(df.sort_values(by="Score", ascending=False))
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Display Technical Charts
st.header("Technical Charts")
for result in results:
    if "Error" in result:
        st.write(f"Error fetching data for {result['Ticker']}: {result['Error']}")
        continue

    data = result["Data"]
    ticker = result["Ticker"]
    
    st.subheader(f"Technical Chart for {ticker}")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data["Close"], label="Close Price", color="blue")
    ax.plot(data.index, data["50_MA"], label="50-Day MA", color="green")
    ax.plot(data.index, data["200_MA"], label="200-Day MA", color="red")
    ax.fill_between(data.index, data["Lower_BB"], data["Upper_BB"], color='gray', alpha=0.2, label="Bollinger Bands")
    ax.legend()
    st.pyplot(fig)
