import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with Stochastic RSI
st.title("Indian Stock Screening Tool with Stochastic RSI")
st.write("""
### Analyze buy, exit, and stop-loss levels using Stochastic RSI for Indian stocks.
""")

# Sidebar for User Input
st.sidebar.header("Input Options")
default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
tickers = st.sidebar.text_area(
    "Enter stock tickers (comma-separated):",
    value=", ".join(default_tickers)
).split(",")

# Function to Calculate Stochastic RSI
def calculate_stoch_rsi(data, period=14):
    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Calculate Stochastic RSI
    stoch_rsi = (rsi - rsi.rolling(window=period).min()) / (rsi.rolling(window=period).max() - rsi.rolling(window=period).min())
    return stoch_rsi

# Function to Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        
        # Calculate Indicators
        data["StochRSI"] = calculate_stoch_rsi(data)
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        # Suggested Levels Based on Stochastic RSI
        def levels_based_on_stoch_rsi(data, stoch_threshold=0.2):
            last_stoch_rsi = data["StochRSI"].iloc[-1]
            buy = data["Lower_BB"].iloc[-1] if last_stoch_rsi < stoch_threshold else None
            exit = data["Upper_BB"].iloc[-1] if last_stoch_rsi > 1 - stoch_threshold else None
            stop_loss = buy * 0.97 if buy else None
            return buy, exit, stop_loss, last_stoch_rsi

        buy_price, exit_price, stop_loss, last_stoch_rsi = levels_based_on_stoch_rsi(data)

        return {
            "Ticker": ticker,
            "Buy Price": round(buy_price, 2) if buy_price else "N/A",
            "Exit Price": round(exit_price, 2) if exit_price else "N/A",
            "Stop Loss": round(stop_loss, 2) if stop_loss else "N/A",
            "StochRSI": round(last_stoch_rsi, 2) if last_stoch_rsi else "N/A",
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
st.header("Stock Screening Results with Stochastic RSI")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Display Technical Charts
st.header("Technical Charts")
for result in results:
    if "Error" in result:
        st.write(f"Error fetching data for {result['Ticker']}: {result['Error']}")
        continue

    ticker = result["Ticker"]
    st.write(f"Stochastic RSI Chart for {ticker}")
    data = yf.Ticker(ticker.strip()).history(period="6mo")
    data["StochRSI"] = calculate_stoch_rsi(data)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data["StochRSI"], label="Stochastic RSI", color="purple")
    ax.axhline(0.2, color="green", linestyle="--", label="Oversold (0.2)")
    ax.axhline(0.8, color="red", linestyle="--", label="Overbought (0.8)")
    ax.legend()
    st.pyplot(fig)
