import yfinance as yf


def get_daily_spot_data():
    """Get daily USDRUB spot quotes from Yahoo."""
    res = yf.download("USDRUB=X", start="2022-01-01", end="2022-03-31",
                      progress=False, interval="1d")\
        .loc[:, "Close"].rename("spot")

    return res
    