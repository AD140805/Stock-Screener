# Fetch and Analyze Data
def fetch_and_analyze_data(ticker):
    try:
        stock = yf.Ticker(ticker.strip())
        data = stock.history(period="6mo")

        # Check for sufficient data
        if len(data) < 20:
            return {"Ticker": ticker, "Error": "Not enough data to compute indicators"}

        # Calculate Indicators
        data["RSI"] = calculate_rsi(data)
        data["ATR"] = calculate_atr(data)
        data["Upper_BB"], data["Lower_BB"] = calculate_bollinger_bands(data)

        # Resample data for weekly and monthly
        data_weekly = data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        data_monthly = data.resample('M').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        # Calculate indicators for weekly and monthly
        data_weekly["RSI"] = calculate_rsi(data_weekly)
        data_weekly["ATR"] = calculate_atr(data_weekly)
        data_weekly["Upper_BB"], data_weekly["Lower_BB"] = calculate_bollinger_bands(data_weekly)

        data_monthly["RSI"] = calculate_rsi(data_monthly)
        data_monthly["ATR"] = calculate_atr(data_monthly)
        data_monthly["Upper_BB"], data_monthly["Lower_BB"] = calculate_bollinger_bands(data_monthly)

        # Timeframe Levels
        def calculate_levels(data_period):
            if len(data_period) < 1:
                return None, None, None  # Return empty levels if data is insufficient

            # Buy Price: Lower Bollinger Band and RSI < 30
            lower_bb = data_period["Lower_BB"].iloc[-1]
            rsi = data_period["RSI"].iloc[-1]
            buy_price = lower_bb if rsi < 30 else data_period["Close"].iloc[-1]  # Default to close price

            # Exit Price: Upper Bollinger Band and RSI > 70
            upper_bb = data_period["Upper_BB"].iloc[-1]
            exit_price = upper_bb if rsi > 70 else data_period["Close"].iloc[-1]  # Default to close price

            # Stop Loss: Buy Price - ATR
            atr = data_period["ATR"].iloc[-1]
            stop_loss = buy_price - atr if buy_price else None

            return buy_price, exit_price, stop_loss

        # Calculate Levels for Different Timeframes
        daily_buy, daily_exit, daily_stop_loss = calculate_levels(data[-1:])
        weekly_buy, weekly_exit, weekly_stop_loss = calculate_levels(data_weekly[-1:])
        monthly_buy, monthly_exit, monthly_stop_loss = calculate_levels(data_monthly[-1:])

        return {
            "Ticker": ticker,
            "Daily Buy": round(daily_buy, 2),
            "Daily Exit": round(daily_exit, 2),
            "Daily Stop Loss": round(daily_stop_loss, 2) if daily_stop_loss else "N/A",
            "Weekly Buy": round(weekly_buy, 2),
            "Weekly Exit": round(weekly_exit, 2),
            "Weekly Stop Loss": round(weekly_stop_loss, 2) if weekly_stop_loss else "N/A",
            "Monthly Buy": round(monthly_buy, 2),
            "Monthly Exit": round(monthly_exit, 2),
            "Monthly Stop Loss": round(monthly_stop_loss, 2) if monthly_stop_loss else "N/A",
            "Data": data
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}
