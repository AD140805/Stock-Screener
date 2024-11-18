import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Web App: Indian Stock Screener with Stochastic RSI and Multi-Timeframes
st.title("Indian Stock Screening Tool with Stochastic RSI and Timeframes")
st.write("""
### Analyze daily, weekly, and monthly buy, exit, and stop-loss levels using Stochastic RSI.
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
        # Fetch historical stock data
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")

        # Ensure data is available
        if data.empty:
            return {"Ticker": ticker, "Error": "No historical data available"}

        # Calculate Indicators
        data["StochRSI"] = calculate_stoch_rsi(data)  # Stochastic RSI
        data["50_MA"] = data["Close"].rolling(window=50).mean()  # 50-day Moving Average
        data["200_MA"] = data["Close"].rolling(window=200).mean()  # 200-day Moving Average
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()  # Upper Bollinger Band
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()  # Lower Bollinger Band

        # Handle cases where Stochastic RSI cannot be calculated
        if data["StochRSI"].isnull().all():
            avg_stoch_rsi = None
        else:
            avg_stoch_rsi = data["StochRSI"].iloc[-1]  # Latest StochRSI value

        # Timeframe-Specific Calculations
        def levels_for_timeframe(data, period, stoch_threshold=0.2):
            data_period = data[-period:]  # Last `period` rows
            if data_period.empty:
                return None, None, None, None  # Fallback for insufficient data

            avg_stoch_rsi = data_period["StochRSI"].mean()

            # Use Bollinger Bands as fallback
            buy = data_period["Lower_BB"].mean()
            exit = data_period["Upper_BB"].mean()
            stop_loss = buy * 0.97 if buy else None  # 3% below buy price

            # Adjust levels based on StochRSI thresholds
            if avg_stoch_rsi is not None:
                if avg_stoch_rsi < stoch_threshold:
                    buy = buy  # Confirm buy level
                else:
                    buy = None
                if avg_stoch_rsi > (1 - stoch_threshold):
                    exit = exit  # Confirm exit level
                else:
                    exit = None

            return buy, exit, stop_loss, avg_stoch_rsi

        # Daily, Weekly, Monthly Levels
        daily_buy, daily_exit, daily_stop_loss, daily_stoch_rsi = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss, weekly_stoch_rsi = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss, monthly_stoch_rsi = levels_for_timeframe(data, 20)

        # Return results as a dictionary
        return {
            "Ticker": ticker,
            "Daily Buy Price": round(daily_buy, 2) if daily_buy else "N/A",
            "Daily Exit Price": round(daily_exit, 2) if daily_exit else "N/A",
            "Daily Stop Loss": round(daily_stop_loss, 2) if daily_stop_loss else "N/A",
            "Daily StochRSI": round(daily_stoch_rsi, 2) if isinstance(daily_stoch_rsi, (int, float)) else "N/A",
            "Weekly Buy Price": round(weekly_buy, 2) if weekly_buy else "N/A",
            "Weekly Exit Price": round(weekly_exit, 2) if weekly_exit else "N/A",
            "Weekly Stop Loss": round(weekly_stop_loss, 2) if weekly_stop_loss else "N/A",
            "Weekly StochRSI": round(weekly_stoch_rsi, 2) if isinstance(weekly_stoch_rsi, (int, float)) else "N/A",
            "Monthly Buy Price": round(monthly_buy, 2) if monthly_buy else "N/A",
            "Monthly Exit Price": round(monthly_exit, 2) if monthly_exit else "N/A",
            "Monthly Stop Loss": round(monthly_stop_loss, 2) if monthly_stop_loss else "N/A",
            "Monthly StochRSI": round(monthly_stoch_rsi, 2) if isinstance(monthly_stoch_rsi, (int, float)) else "N/A",
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
st.header("Stock Screening Results with Stochastic RSI and Timeframes")
if not df.empty:
    st.dataframe(df)
    st.download_button("Download Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Display Stochastic RSI Charts
st.header("Stochastic RSI Charts")
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
