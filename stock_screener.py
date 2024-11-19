import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(page_title="Stock Screener", page_icon="📈", layout="wide")

# App Title
st.title("📊 Indian Stock Screening Tool")
st.markdown("""
Analyze **daily**, **weekly**, and **monthly** buy, sell, and stop-loss ranges for Indian stocks.
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

        # Debug: Check raw data
        if len(data) < 20:
            return {"Ticker": ticker, "Error": "Not enough data to calculate indicators"}
        
        st.write(f"Raw Data for {ticker}:", data.tail())  # Debugging

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data).fillna(50)
        data["50_MA"] = data["Close"].rolling(window=50).mean().fillna(method='bfill')
        data["200_MA"] = data["Close"].rolling(window=200).mean().fillna(method='bfill')
        data["Upper_BB"] = (data["Close"].rolling(window=20).mean() + 2 * data["Close"].rolling(window=20).std()).fillna(method='bfill')
        data["Lower_BB"] = (data["Close"].rolling(window=20).mean() - 2 * data["Close"].rolling(window=20).std()).fillna(method='bfill')

        # Calculate Ranges
        def calculate_ranges(data_period):
            if data_period.empty:
                return None, None, None
            buy = data_period["Lower_BB"].mean()
            sell = data_period["Upper_BB"].mean()
            stop_loss = buy * 0.97
            return buy, sell, stop_loss

        # Distinct Timeframes
        daily_data = data[-1:]
        weekly_data = data[-5:]
        monthly_data = data[-20:]

        daily_buy, daily_sell, daily_stop_loss = calculate_ranges(daily_data)
        weekly_buy, weekly_sell, weekly_stop_loss = calculate_ranges(weekly_data)
        monthly_buy, monthly_sell, monthly_stop_loss = calculate_ranges(monthly_data)

        # Handle Missing or Invalid Values
        if not daily_buy or not daily_sell:
            daily_buy, daily_sell = 0, 0
        if not weekly_buy or not weekly_sell:
            weekly_buy, weekly_sell = 0, 0
        if not monthly_buy or not monthly_sell:
            monthly_buy, monthly_sell = 0, 0

        return {
            "Ticker": ticker,
            "Daily Buy Range": (round(daily_buy * 0.98, 2), round(daily_buy * 1.02, 2)),
            "Daily Sell Range": (round(daily_sell * 0.98, 2), round(daily_sell * 1.02, 2)),
            "Daily Stop Loss": round(daily_stop_loss, 2),
            "Weekly Buy Range": (round(weekly_buy * 0.98, 2), round(weekly_buy * 1.02, 2)),
            "Weekly Sell Range": (round(weekly_sell * 0.98, 2), round(weekly_sell * 1.02, 2)),
            "Weekly Stop Loss": round(weekly_stop_loss, 2),
            "Monthly Buy Range": (round(monthly_buy * 0.98, 2), round(monthly_buy * 1.02, 2)),
            "Monthly Sell Range": (round(monthly_sell * 0.98, 2), round(monthly_sell * 1.02, 2)),
            "Monthly Stop Loss": round(monthly_stop_loss, 2),
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
        st.dataframe(df[["Ticker", "Daily Buy Range", "Daily Sell Range", "Daily Stop Loss"]])

    with tab2:
        st.dataframe(df[["Ticker", "Weekly Buy Range", "Weekly Sell Range", "Weekly Stop Loss"]])

    with tab3:
        st.dataframe(df[["Ticker", "Monthly Buy Range", "Monthly Sell Range", "Monthly Stop Loss"]])

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
