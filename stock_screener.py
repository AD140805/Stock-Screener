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

# User Input: Stock Ti
