import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Stock Screener", page_icon="📈", layout="wide")

# App Title
st.title("📊 Indian Stock Screening Tool")
st.markdown("""
Analyze **daily**, **weekly**, and **monthly** buy, exit, and stop-loss levels for Indian stocks.
""")

# Sidebar for Stock Input
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

# Fetch and Analyze Stock Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")
        
        # Calculate Indicators
        data["RSI"] = calculate_rsi(data)
        data["50_MA"] = data["Close"].rolling(window=50).mean()
        data["200_MA"] = data["Close"].rolling(window=200).mean()
        data["Upper_BB"] = data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()
        data["Lower_BB"] = data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()

        # Timeframe Levels
        def levels_for_timeframe(data, period):
            data_period = data[-period:]
            buy = data_period["Lower_BB"].mean()
            exit = data_period["Upper_BB"].mean()
            stop_loss = buy * 0.97
            avg_rsi = data_period["RSI"].mean()
            return buy, exit, stop_loss, avg_rsi

        daily_buy, daily_exit, daily_stop_loss, daily_rsi = levels_for_timeframe(data, 1)
        weekly_buy, weekly_exit, weekly_stop_loss, weekly_rsi = levels_for_timeframe(data, 5)
        monthly_buy, monthly_exit, monthly_stop_loss, monthly_rsi = levels_for_timeframe(data, 20)

        return {
            "Ticker": ticker,
            "Daily Buy": round(daily_buy, 2),
            "Daily Exit": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2),
            "Daily RSI": round(daily_rsi, 2),
            "Weekly Buy": round(weekly_buy, 2),
            "Weekly Exit": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2),
            "Weekly RSI": round(weekly_rsi, 2),
            "Monthly Buy": round(monthly_buy, 2),
            "Monthly Exit": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2),
            "Monthly RSI": round(monthly_rsi, 2),
            "Data": data
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Fetch and Analyze Data for All Tickers
results = [fetch_and_analyze_data(ticker) for ticker in tickers]

# Results Table
summary = [
    {k: v for k, v in res.items() if k != "Data"} for res in results if "Error" not in res
]
df = pd.DataFrame(summary)

# Tabs for Display
st.header("📋 Stock Screening Results")
if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📈 Daily Levels", "📉 Weekly Levels", "📊 Monthly Levels"])

    with tab1:
        st.dataframe(df[["Ticker", "Daily Buy", "Daily Exit", "Daily Stop Loss", "Daily RSI"]])

    with tab2:
        st.dataframe(df[["Ticker", "Weekly Buy", "Weekly Exit", "Weekly Stop Loss", "Weekly RSI"]])

    with tab3:
        st.dataframe(df[["Ticker", "Monthly Buy", "Monthly Exit", "Monthly Stop Loss", "Monthly RSI"]])

    st.download_button("📥 Download All Results as CSV", df.to_csv(index=False), "stock_screening_results.csv")

# Chart Display
st.header("📊 Technical Charts")
for res in results:
    if "Error" in res:
        st.warning(f"Error fetching data for {res['Ticker']}: {res['Error']}")
        continue

    data = res["Data"]
    ticker = res["Ticker"]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode='lines', name="Close Price"))
    fig.add_trace(go.Scatter(x=data.index, y=data["50_MA"], mode='lines', name="50-Day MA"))
    fig.add_trace(go.Scatter(x=data.index, y=data["200_MA"], mode='lines', name="200-Day MA"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Upper_BB"], mode='lines', name="Upper Bollinger Band"))
    fig.add_trace(go.Scatter(x=data.index, y=data["Lower_BB"], mode='lines', name="Lower Bollinger Band"))

    fig.update_layout(title=f"Technical Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
    st.plotly_chart(fig)
