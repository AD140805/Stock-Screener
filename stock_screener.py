import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="TradingView-Like Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add Custom CSS for TradingView-like Styling
st.markdown("""
    <style>
        /* General Layout */
        .main { background-color: #f4f4f4; color: #333; font-family: 'Arial', sans-serif; }
        footer { visibility: hidden; }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] { background-color: #1c1c1e; color: white; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #e6e6e6;
        }
        
        /* Chart Background */
        .plotly-graph-div { background: #1f1f22; border-radius: 10px; padding: 10px; }

        /* Buttons */
        .stButton button {
            background-color: #00bfff;
            color: white;
            border: none;
            border-radius: 5px;
        }
        .stButton button:hover {
            background-color: #007acc;
        }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("📊 TradingView-Like Indian Stock Screener")
st.markdown("""
**Analyze Indian stocks with interactive charts, dynamic buy/sell ranges, and key indicators.**  
Experience the aesthetic and functionality of TradingView directly in this app!
""")

# Sidebar for Stock Input
with st.sidebar:
    st.header("Stock Input Options")
    default_tickers = ["TCS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    tickers = st.text_area(
        "Enter stock tickers (comma-separated):",
        value=", ".join(default_tickers),
        help="Use NSE tickers (e.g., TCS.NS, RELIANCE.NS). Separate tickers with commas."
    ).split(",")

    tickers = [ticker.strip().upper() for ticker in tickers if ticker.strip()]

# Function: Fetch and Analyze Stock Data
@st.cache_data
def fetch_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1y")
        if data.empty:
            return None
        data['50_MA'] = data['Close'].rolling(window=50).mean()
        data['200_MA'] = data['Close'].rolling(window=200).mean()
        return data
    except Exception:
        return None

# Display Stock Data and Charts
if tickers:
    results = []
    for ticker in tickers:
        st.subheader(f"📈 {ticker} Technical Analysis")
        
        data = fetch_stock_data(ticker)
        if data is not None:
            # Save results for potential CSV download
            results.append({
                "Ticker": ticker,
                "Latest Close": round(data['Close'].iloc[-1], 2),
                "50_MA": round(data['50_MA'].iloc[-1], 2) if not pd.isna(data['50_MA'].iloc[-1]) else "N/A",
                "200_MA": round(data['200_MA'].iloc[-1], 2) if not pd.isna(data['200_MA'].iloc[-1]) else "N/A",
            })

            # Interactive Chart with Plotly
            fig = go.Figure()

            # Close Price Line
            fig.add_trace(go.Scatter(
                x=data.index, y=data['Close'],
                mode='lines', name="Close Price",
                line=dict(color="#00bfff", width=2)
            ))

            # Moving Averages
            fig.add_trace(go.Scatter(
                x=data.index, y=data['50_MA'],
                mode='lines', name="50-Day MA",
                line=dict(color="#ffbf00", width=1.5, dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=data.index, y=data['200_MA'],
                mode='lines', name="200-Day MA",
                line=dict(color="#ff4d4d", width=2, dash='dot')
            ))

            # Volume as Bar Chart
            fig.add_trace(go.Bar(
                x=data.index, y=data['Volume'],
                name="Volume", marker=dict(color="#999999", opacity=0.6)
            ))

            # Layout Customization for TradingView-like Look
            fig.update_layout(
                title=f"Technical Chart: {ticker}",
                xaxis_title="Date",
                yaxis_title="Price",
                yaxis=dict(showgrid=False),
                xaxis=dict(showgrid=False),
                template="plotly_dark",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=600
            )

            st.plotly_chart(fig)
        else:
            st.warning(f"Could not fetch data for {ticker}. Please check the ticker symbol.")

    # Display Summary Table
    if results:
        st.header("📋 Summary Table")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)
        st.download_button(
            label="📥 Download Results as CSV",
            data=results_df.to_csv(index=False),
            file_name="stock_screener_results.csv",
            mime="text/csv"
        )
else:
    st.info("Please enter stock tickers in the sidebar to begin analysis.")

# Footer or Branding (Optional)
st.markdown("""
    <div style="text-align: center; margin-top: 30px; color: #888;">
        Built with ❤️ using <b>Streamlit</b> | Inspired by <b>TradingView</b>
    </div>
""", unsafe_allow_html=True)
