import pandas as pd
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from scipy.integrate import simps
from functools import reduce
from tensorflow_probability import distributions as tfd

from optools.blackscholes import option_price as bs_price
from optools.volsmile import VolatilitySmile
from optools.rnd import fit_lognormal_mix


def mf_prob_estimator(df_: pd.DataFrame):
    """Estimate rn prob of S>85.

    Parameters
    ----------
    df_
        from pd.groupby; with columns 'forward', 'div_yield' etc.

    Returns
    -------

    """
    x = np.arange(85, 150, 1e-04)
    f_ = df_["forward"].iloc[0]
    r_ = df_[["rf", "div_yield"]].iloc[0]

    vs = VolatilitySmile(
        vol_series=df_[["strike", "vol"]].set_index("strike").squeeze(),
        tau=1/12
    )

    # differentiate w.r.t. K to ged the rnd
    rnd_func = vs.get_rnd(forward=f_, is_call=True, **r_)

    # integrate
    res = simps(rnd_func(x), x)

    return res


def lnmix_prob_estimator(df_: pd.DataFrame):
    """
    """
    f_ = df_["forward"].iloc[0]
    r_ = df_[["rf", "div_yield"]].iloc[0]
    k_, v_ = df_["strike"].values, df_["vol"].values

    # compute option prices first
    c_price = bs_price(
        strike=k_, vol=v_, forward=f_,
        rf=r_["rf"], div_yield=r_["div_yield"],
        is_call=True, tau=1/12
    )

    # initial values
    x0_ = np.array(
        [0.34] + [np.log(f_) - v_.mean() ** 2 / 2] * 2 + [v_.mean()] * 2
    )

    # fit!
    theta = fit_lognormal_mix(
        option_price=c_price, strike=k_, is_call=True,
        forward=f_, rf=r_["rf"],
        x0=x0_, weights=np.array([2, 1, 1, 1, 1, 1])
    )

    rnd = tfd.Mixture(
        cat=tfd.Categorical(probs=[theta[0], 1. - theta[0]]),
        components=[
            tfd.LogNormal(loc=theta[1], scale=theta[3]),
            tfd.LogNormal(loc=theta[2], scale=theta[4]),
        ]
    )

    res = 1 - rnd.cdf(85).numpy()

    # res = pd.Series(mfit, index=["w", "mu1", "mu2", "sigma1", "sigma2"])

    return res


def estimate_probability(strikes_vola, forward, rates,
                         kind="parametric", parallelize=False) \
        -> pd.Series:
    """Estimate parameters of the mixture of 2 log-normals.

    Assumes maturity of options and forwards to be 1/12.

    Parameters
    ----------
    strikes_vola
    forward
    rates
        in frac of 1 p.a.
    kind : str
        'parametric' or 'model-free'
    parallelize : bool
        True to parallelize
    """
    # drop dates with <5 observations
    n_per_date = strikes_vola.groupby("date").count().iloc[:, 0]
    good_dt = n_per_date.loc[n_per_date.gt(4)].index

    # merge all the necessary data (produces duplicates for some vars)
    data = reduce(
        lambda x_, y_: pd.merge(x_, y_, on="date", how="inner"),
        [strikes_vola, forward, rates]
    )
    data = data.loc[data["date"].isin(good_dt)].sort_values("date")

    # function to apply in parallel
    def apply_parallel(grp, func):
        with Pool(cpu_count()) as p:
            ret_list = p.map(func, [group for name, group in grp])
        res_ = pd.Series(ret_list, index=[n_ for n_, _ in grp])
        return res_

    if kind.startswith("param"):
        func_to_apply = lnmix_prob_estimator
    else:
        func_to_apply = mf_prob_estimator

    if parallelize:
        res = apply_parallel(data.groupby("date"), func_to_apply)
    else:
        res = dict()
        for dt, dt_grp in tqdm(data.groupby("date")):
            res[dt] = func_to_apply(dt_grp)
        res = pd.Series(res)

    return res
