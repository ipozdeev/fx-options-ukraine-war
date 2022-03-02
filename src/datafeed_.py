import os

import pandas as pd

from .setup import *

DATAPATH = os.path.join(os.environ.get("PROJECT_ROOT"), "data/")


def get_spot_data() -> pd.DataFrame:
    """Get USDRUB spot rates."""
    fname = os.path.join(DATAPATH, "spot.ftr")
    res = pd.read_feather(fname)\
        .set_index("date").resample("1T").asfreq()\
        .reset_index()
    return res


def get_ois_data() -> pd.DataFrame:
    """Get 1-month and 1-week USD OIS rates, in percent p.a."""
    fname = os.path.join(DATAPATH, "ois.ftr")
    return pd.read_feather(fname)


def get_forward_data() -> pd.DataFrame:
    """Get 1-month and 1-week USDRUB forward rates."""
    fname = os.path.join(DATAPATH, "forward.ftr")
    return pd.read_feather(fname)


def get_option_data() -> pd.DataFrame:
    """Get IV for 10- and 25-delta calls and puts, as well as ATM IV.

    In percent p.a.

    """
    fname = os.path.join(DATAPATH, "option.ftr")
    return pd.read_feather(fname)


def get_timeline() -> pd.Series:
    """
    """
    fname = os.path.join(DATAPATH, "timeline.csv")
    res = pd.read_csv(fname, index_col=0, parse_dates=True)
    return res
