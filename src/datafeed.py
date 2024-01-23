import pandas as pd
from pathlib import Path
import os

# settings
DATA_PATH = Path(os.environ.get("CONTENT_ROOT", ".")) / "data"


def get_timeline() -> pd.DataFrame:
    """Get events."""
    fname = DATA_PATH / "raw" / "timeline.csv"
    res = pd.read_csv(fname, index_col=0, parse_dates=True)\
        .sort_index()

    return res


def process_raw_data(filename: str, rates_ann_factor: float) -> None:
    """Process raw high frequency data.

    Introduces new variable 'r_counter' that is the risk-free rate implied by
    the forward-spot parity and 'r_base' found in the raw data `filename`;
    converts rates and volatilities from percent to frac of 1. Stores the
    processed data as data/processed/data.ftr

    Parameters
    ----------
    filename : str
        path relative to data/raw, referencing a .ftr pyarrow file,
        e.g. 'usdrub-data-hf.ftr'; therein is stored a long-form dataframe
        with columns ['date', 'name', 'value']; (name, value) pairs are:
            - 'spot': XXXRUB spot rate
            - 'forward': XXXRUB 1-month forward rate
            - 'v_atm': volatility of 1-month ATM contracts, in percent.
            - 'v_25r': quote of 25-delta risk reversal, in percent
            - 'v_10r': quote of 10-delta risk reversal, in percent
            - 'v_25b': quote of 25-delta butterfly spread (market strangle),
                in percent
            - 'v_10b': quote of 10-delta butterfly spread (market strangle),
                in percent
            - 'r_base': risk-free rate in XXX, in percent.
        A sample:
                                   date     name     value
            0 2022-02-28 16:44:00+01:00     spot    109.31
            1 2022-02-28 16:44:00+01:00   r_base      0.24
            2 2022-02-28 16:44:00+01:00    v_atm     85.48
            3 2022-02-28 16:44:00+01:00    v_25r     21.32
            4 2022-02-28 16:44:00+01:00    v_10r     46.03
            5 2022-02-28 16:44:00+01:00    v_25b      3.77
            6 2022-02-28 16:44:00+01:00    v_10b     14.67
            7 2022-02-28 16:44:00+01:00  forward    112.44

    rates_ann_factor : float
        annualization factor for interest rates, depending on the maturity
        of the derivatives and the days count convention for the rate;
        for example, when derivatives mature in 30 days and the interest rate
        is the USD OIS (the day count is ACT/360), `rates_ann_factor` = 360/30;
        will be used to de-annualize the rates as `r_ann / rates_ann_factor`
    """
    data = pd.read_feather(filename)\
        .pivot(index="date", columns="contract", values="value")

    # calculate interest rate for the counter currency
    # f = s * (1 + r_counter) / (1 + r_base)
    data["r_counter"] = (
           data["forward"] / data["spot"] *
               (1 + data["r_base"] / 100 / rates_ann_factor)
           - 1
    ) * rates_ann_factor

    # store
    data.to_feather(DATA_PATH / "processed" / "data.ftr")


def get_daily_spot_data(excel_filename):
    """"""
    res = pd.read_excel(excel_filename, sheet_name="spot", skiprows=3,
                        index_col=0, parse_dates=True)\
        .iloc[:, 0].rename("spot")

    return res
    