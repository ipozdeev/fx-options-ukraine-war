import os
import pandas as pd


def get_processed_data() -> pd.DataFrame:
    """Get data necessary to calculate risk-neutral probability.

    Reads .ftr called usdrub-data-raw.ftr that contains the values of
        - 'date': datetime64[ns, Europe/Zurich], timezone-aware dates
        - 'spot': XXXRUB spot rate
        - 'forward': XXXRUB 1-month forward rate
        - 'v_atm': volatility of 1-month ATM contracts, in frac of 1 p.a.
        - 'v_25r': quote of 25-delta risk reversal
        - 'v_10r': quote of 10-delta risk reversal
        - 'v_25b': quote of 25-delta butterfly spread (market strangle)
        - 'v_10b': quote of 10-delta butterfly spread (market strangle)
        - 'r_counter': risk-free rate in RUB, in frac of 1 p.a.
        - 'r_base': risk-free rate in XXX, in frac of 1 p.a.

    It is possible for the risk-free rate to be implied by forward prices.

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
    fname = PROCESSED_DATA_PATH / "data.ftr"
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
    data = get_processed_data()
    res = data.loc[data["name"].str.startswith("v_")]

    return res


def get_spot_data() -> pd.DataFrame:
    """Get USDRUB spot rates."""
    res = get_processed_data()\
        .query("name == 'spot'") \
        .pivot(index="date", columns="name", values="value") \
        .reset_index()

    return res


def get_rates_data() -> pd.DataFrame:
    """Get 1-month USD ('div_yield') and RUB ('rf') rates, in percent p.a.

    USD are OIS-rates, RUB rates are forward-implied.

    """
    res = get_processed_data() \
        .query("name == ('r_counter', 'r_base')") \
        .pivot(index="date", columns="name", values="value")\
        .reset_index()
    return res


def get_forward_data() -> pd.DataFrame:
    """Get 1-month and 1-week USDRUB forward rates."""
    res = get_processed_data() \
        .query("name == 'forward'") \
        .pivot(index="date", columns="name", values="value") \
        .reset_index()

    return res


def get_timeline() -> pd.DataFrame:
    """Get events."""
    fname = os.path.join(PROCESSED_DATA_PATH, "timeline.csv")
    res = pd.read_csv(fname, index_col=0, parse_dates=True)

    return res


def get_raw_data_from_xlsx(filename: str, maturity: str):
    """"""
    meta = pd.read_excel(filename, sheet_name="meta", index_col=0)

    data = pd.read_excel(filename, sheet_name=[maturity, "spot"], skiprows=3,
                         index_col=0, parse_dates=True)

    spot = data["spot"].iloc[:, 0].rename("spot")

    # take the sheet with instruments of chosen maturity
    instruments = data[maturity].rename(
        columns=meta.loc[maturity].reset_index().set_index(maturity).iloc[:, 0]
    )

    # from fwd points to fwd outrights
    instruments["fwd"] = spot + instruments["fwd"] / 10000

    # rates and volas from % to frac of 1
    instruments[["r_foreign", "b10", "b25", "r10", "r25", "b15", "b35", "r15",
                 "r35"]] /= 100

    # calculate interest rate for the counter currency
    # f = s * (1 + r_counter) / (1 + r_base)
    days_to_maturity = {"1m": 30, "3m": 91}.get(maturity)
    instruments["r_counter"] = (
        instruments["fwd"] / spot *
        (1 + instruments["r_foreign"] / 100 / 360 * days_to_maturity)
        - 1
    ) * 360 / days_to_maturity

    # name of the file
    processed_fname = f"data/processed/data-{maturity}.ftr"

    instruments.rename(columns={"fwd": "forward", "atmv": "v_atm",
                        "b10": "v_10b", "b15": "v_15b",
                        "b25": "v_25b", "b35": "v_35b",
                        "r10": "v_10r", "r15": "v_15r",
                        "r25": "v_25r", "r35": "v_35r",
                        "r_foreign": "r_base"})\
        .rename_axis(index="date")\
        .reset_index()\
        .melt(id_vars="date", var_name="name", value_name="value")\
        .to_feather(processed_fname)


def process_raw_data(filename: str, rates_ann_factor: float) -> None:
    """Process raw data.

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
            0 2022-02-28 16:44:00+01:00     spot  109.3052
            1 2022-02-28 16:44:00+01:00   r_base    0.2354
            2 2022-02-28 16:44:00+01:00    v_atm   85.4825
            3 2022-02-28 16:44:00+01:00    v_25r   21.3200
            4 2022-02-28 16:44:00+01:00    v_10r   46.0300
            5 2022-02-28 16:44:00+01:00    v_25b    3.7750
            6 2022-02-28 16:44:00+01:00    v_10b   14.6675
            7 2022-02-28 16:44:00+01:00  forward  112.4394
    rates_ann_factor : float
        annualization factor for interest rates, depending on the maturity
        of the derivatives and the days count convention for the rate;
        for example, when derivatives mature in 30 days and the interest rate
        is the USD OIS (the day count is ACT/360), `rates_ann_factor` = 360/30;
        will be used to de-annualize the rates as `r_ann / rates_ann_factor`
    """
    data = pd.read_feather(filename)\
        .pivot(index="date", columns="name", values="value")

    # calculate interest rate for the counter currency
    # f = s * (1 + r_counter) / (1 + r_base)
    data["r_counter"] = (
           data["forward"] / data["spot"] *
               (1 + data["r_base"] / 100 / rates_ann_factor)
           - 1
    ) * rates_ann_factor

    # store
    data.to_feather("data/processed")
