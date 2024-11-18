import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with RSI
st.title("Indian Stock Screening Tool with RSI")
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

# Function to Calculate RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        # Fetch historical stock data
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")

        # Ensure data is available
        if data.empty:
            return {"Ticker": ticker, "Error": "No historical data available"}

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data)  # RSI
        data["50_MA"] = data["Close"].rolling(window=50).mean()  # 50-day Moving Average
        data["200_MA"] = data["Close"].rolling(window=200).mean()  # 200-day Moving Average
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()  # Upper Bollinger Band
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()  # Lower Bollinger Band

        # Handle cases where RSI cannot be calculated
        if data["RSI"].isnull().all():
            avg_rsi = None
        else:
            avg_rsi = data["RSI"].iloc[-1]  # Latest RSI value

        # Timeframe-Specific Calculations
        def levels_for_timeframe(data, period):
            data_period = data[-period:]  # Last `period` rows
            if data_period.empty:
                return None, None, None, None  # Fallback for insufficient data

            avg_rsi = data_period["RSI"].mean()

            # Use Bollinger Bands for levels
            buy = data_period["Lower_BB"].mean() if avg_rsi < 30 else None
            exit = data_period["Upper_BB"].mean() if avg_rsi > 70 else None
            stop_loss = buy * 0.97 if buy else None  # 3% below buy price

            return buy, exit, stop_loss, avg_rsi

        # Daily, Weekly, Monthly Levels
        daily_buy, daily_exit, daily_stop_loss, daily_rsi = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss, weekly_rsi = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss, monthly_rsi = levels_for_timeframe(data, 20)

        # Return results as a dictionary
        return {
            "Ticker": ticker,
            "Daily Buy Price": round(daily_buy, 2) if daily_buy else "N/A",
            "Daily Exit Price": round(daily_exit, 2) if daily_exit else "N/A",
            "Daily Stop Loss": round(daily_stop_loss, 2) if daily_stop_loss else "N/A",
            "Daily RSI": round(daily_rsi, 2) if isinstance(daily_rsi, (int, float)) else "N/A",
            "Weekly Buy Price": round(weekly_buy, 2) if weekly_buy else "N/A",
            "Weekly Exit Price": round(weekly_exit, 2) if weekly_exit else "N/A",
            "Weekly Stop Loss": round(weekly_stop_loss, 2) if weekly_stop_loss else "N/A",
            "Weekly RSI": round(weekly_rsi, 2) if isinstance(weekly_rsi, (int, float)) else "N/A",
            "Monthly Buy Price": round(monthly_buy, 2) if monthly_buy else "N/A",
            "Monthly Exit Price": round(monthly_exit, 2) if monthly_exit else "N/A",
            "Monthly Stop Loss": round(monthly_stop_loss, 2) if monthly_stop_loss else "N/A",
            "Monthly RSI": round(monthly_rsi, 2) if isinstance(monthly_rsi, (int, float)) else "N/A",
        }
    except Exception as e:
        # Return the error for debugging
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Convert Results to DataFrame
summary = [
    {k: v for k, v in res.items()} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)

# Display Results
st.header("Stock Screening Results with RSI")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Display RSI Charts
st.header("RSI Charts")
for result in results:
    if "Error" in result:
        st.write(f"Error fetching data for {result['Ticker']}: {result['Error']}")
        continue

    ticker = result["Ticker"]
    st.write(f"RSI Chart for {ticker}")
    data = yf.Ticker(ticker.strip()).history(period="6mo")
    data["RSI"] = calculate_rsi(data)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data["RSI"], label="RSI", color="blue")
    ax.axhline(30, color="green", linestyle="--", label="Oversold (30)")
    ax.axhline(70, color="red", linestyle="--", label="Overbought (70)")
    ax.legend()
    st.pyplot(fig)
