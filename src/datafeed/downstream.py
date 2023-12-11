import os
import pandas as pd

DATAPATH = "data/"


def get_raw_data() -> pd.DataFrame:
    """Get data necessary to calculate risk-neutral probability.

    Reads .ftr called usdrub-data-raw.ftr that contains the values of
        'spot': USDRUB spot rate
        'forward': USDRUB 1-month forward rate
        'v_atm': volatility of 1-month ATM contracts, in frac of 1 p.a.
        'v_25r': quote of 25-delta risk reversal
        'v_10r': quote of 10-delta risk reversal
        'v_25b': quote of 25-delta butterfly spread (market strangle)
        'v_10b': quote of 10-delta butterfly spread (market strangle)
        'r_counter': risk-free rate in RUB, in frac of 1 p.a.
        'r_base': risk-free rate in USD, in frac of 1 p.a.

    sample:
                               date       name       value
        0 2022-02-28 16:44:00+01:00    forward  112.439400
        1 2022-02-28 16:44:00+01:00     r_base    0.002354
        2 2022-02-28 16:44:00+01:00  r_counter    0.346508
        3 2022-02-28 16:44:00+01:00       spot  109.305200
        4 2022-02-28 16:44:00+01:00      v_10b    0.146675
        5 2022-02-28 16:44:00+01:00      v_10r    0.460300
        6 2022-02-28 16:44:00+01:00      v_25b    0.037750
        7 2022-02-28 16:44:00+01:00      v_25r    0.213200
        8 2022-02-28 16:44:00+01:00      v_atm    0.854825

    Returns
    -------
    pd.DataFrame
        with columns
            'date': datetime64[ns, Europe/Zurich]
            'name': object
            'value': float64
    """
    fname = os.path.join(DATAPATH, "usdrub-data-raw.ftr")
    res = pd.read_feather(fname)
    return res


def get_option_contracts_data() -> pd.DataFrame:
    """Get option contracts data, in long form.

    for each date, gets 5 implied vola quotes: at-the-money, 25- and
    10-delta butterfly spreads (aka market strangles) and risk reversals.

    Returns
    -------
    pd.DataFrame
        with columns:
            date: datetime64[ns, Europe/Zurich], timezone-aware dates
            name: str, isin(['v_atm', 'v_25r', 'v_10r', 'v_25b', 'v_10b'])
            value: float64, in frac of 1 p.a.

    """
    data = get_raw_data()
    res = data.loc[data["name"].str.startswith("v_")]

    return res


def get_spot_data() -> pd.DataFrame:
    """Get USDRUB spot rates."""
    res = get_raw_data()\
        .query("name == 'spot'") \
        .pivot(index="date", columns="name", values="value") \
        .reset_index()

    return res


def get_rates_data() -> pd.DataFrame:
    """Get 1-month USD ('div_yield') and RUB ('rf') rates, in percent p.a.

    USD are OIS-rates, RUB rates are forward-implied.

    """
    res = get_raw_data() \
        .query("name == ('r_counter', 'r_base')") \
        .pivot(index="date", columns="name", values="value")\
        .reset_index()
    return res


def get_forward_data() -> pd.DataFrame:
    """Get 1-month and 1-week USDRUB forward rates."""
    res = get_raw_data() \
        .query("name == 'forward'") \
        .pivot(index="date", columns="name", values="value") \
        .reset_index()

    return res


def get_timeline() -> pd.DataFrame:
    """Get events."""
    fname = os.path.join(DATAPATH, "timeline.csv")
    res = pd.read_csv(fname, index_col=0, parse_dates=True)

    return res
