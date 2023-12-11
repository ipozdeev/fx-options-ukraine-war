import os
import pandas as pd
import numpy as np

from optools.strike import strike_from_delta, strike_from_atm

from .downstream import *

DATAPATH = os.path.join(os.environ.get("PROJECT_ROOT"), "data/")


def put_raw_data() -> None:
    """
    """
    # excel
    # read in
    fname = os.path.join(DATAPATH, "RUB1M_BB_ticks.xlsx")
    data = pd.read_excel(fname, header=None)

    # loop over pairs of columns
    res = dict()
    for p in range(0, data.shape[1], 3):
        chunk = data.iloc[4:, p:p+2].dropna().iloc[:-1].set_index(p).squeeze()
        chunk.index = pd.to_datetime(chunk.index).tz_localize("Europe/Zurich")\
            .rename("date")
        res[(data.iloc[2, p], data.iloc[0, p+1])] = chunk
    res = pd.concat(res, axis=1).xs("Trade", axis=1, level=1)
    res.columns = ["spot", "ois", "v_atm", "v_25r", "v_10r", "v_25b",
                   "v_10b", "forward"]
    res.loc[:, ["v_atm", "v_25r", "v_10r", "v_25b", "v_10b"]] /= 100
    res.loc[:, "ois"] /= 100
    res.loc[:, "forward"] = res["forward"] / 10000 + res["spot"]
    res.loc[:, "rf"] = (
        res["forward"] / res["spot"] * (1 + res["ois"] / 12)
    ).sub(1).mul(12)
    res = res.rename(columns={"ois": "div_yield"})

    # save
    res.reset_index().melt(id_vars="date", var_name="name")\
        .dropna().reset_index(drop=True)\
        .to_feather(os.path.join(DATAPATH, "usdrub-data-raw.ftr"))

    # # csv
    # fname = os.path.join(DATAPATH, "usdrub-data.csv")
    # data = pd.read_csv(fname, usecols=["date", "name", "maturity", "value"])
    # data.loc[:, "maturity"] = data["maturity"] \
    #     .map(dict(zip(data["maturity"].unique(), ("1w", "1m"))))
    # data.loc[:, "date"] = pd.to_datetime(data["date"]) \
    #     .dt.tz_localize("Europe/Zurich")
    #
    # # spot
    # spot = data.query("name == 'Spot'").pivot("date", "maturity", "value") \
    #            .bfill(axis=1).loc[:, "1m"]
    # spot = spot.where(spot.diff() != 0).dropna()
    # spot.rename("value").reset_index() \
    #     .to_feather(os.path.join(DATAPATH, "spot.ftr"))
    #
    # # forward
    # forward = data.query("name == 'Outright'") \
    #               .pivot("date", "maturity", "value") \
    #               .loc[:, "1m"].reindex(index=spot.index).dropna()
    # forward.rename("value").reset_index() \
    #     .to_feather(os.path.join(DATAPATH, "forward.ftr"))
    #
    # # ois
    # ois = data.query("name == 'OIS'") \
    #           .pivot("date", "maturity", "value") \
    #           .ffill(limit=2) \
    #           .loc[:, "1m"].reindex(index=spot.index).dropna()
    # ois.rename("value").reset_index() \
    #     .to_feather(os.path.join(DATAPATH, "ois.ftr"))
    #
    # # options
    # opt = data.query("name == ('C10', 'C25', 'P10', 'P25', 'ATM') & "
    #                  "maturity == '1m'")


def put_strikes_data() -> None:
    d_full = get_raw_data()
    d_full = d_full.pivot(index="date", columns="name", values="value")
    v_10 = vanillas_from_combinations(r=d_full["v_10r"], b=d_full["v_10b"],
                                      atm_vol=d_full["v_atm"], delta=0.1)
    v_25 = vanillas_from_combinations(r=d_full["v_25r"], b=d_full["v_25b"],
                                      atm_vol=d_full["v_atm"], delta=0.25)

    vol = pd.concat({**v_10, **v_25}, axis=0, names=["delta"]).rename("vol") \
        .reset_index().pivot(index="date", columns="delta", values="vol")
    v_data = pd.concat(
        (vol, d_full[["forward", "rf", "v_atm", "spot", "div_yield"]]),
        axis=1
    ).dropna()

    def strike_getter(x_):
        res_ = strike_from_delta(tau=1/12,
                                 is_call=True, is_forward=False,
                                 is_premiumadj=True,
                                 **x_.drop(["v_atm", "date"]))
        return res_[0]

    # k = v_data.query("date == '2022-02-28 16:27:00+01:00'")\
    #     .apply(strike_getter, axis=1).reset_index().rename(columns=str)
    v_data = v_data\
        .reset_index()\
        .melt(id_vars=["date", "spot", "div_yield", "rf", "v_atm", "forward"],
              var_name="delta", value_name="vol")
    k = v_data.apply(strike_getter, axis=1)
    k = pd.concat((k.rename("strike"), v_data[["date", "vol"]]),
                  axis=1)

    # atm delta + strike
    k_atm = strike_from_atm("dns", is_premiumadj=True, spot=d_full["spot"],
                            forward=d_full["forward"], vola=d_full["v_atm"],
                            tau=1/12)
    k_atm = pd.concat((k_atm.rename("strike"), d_full["v_atm"].rename("vol")),
                      axis=1).reset_index()

    pd.concat((k, k_atm))\
        .dropna() \
        .reset_index(drop=True) \
        .to_feather(os.path.join(DATAPATH, "strike-vola.ftr"))
