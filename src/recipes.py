import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from scipy.integrate import simps
from joblib import Memory
from itertools import product

from optools.smile import SABR

memory = Memory(location=os.path.join(os.environ.get("PROJECT_ROOT"), "data"),
                verbose=False)


@memory.cache
def sabr_getter(chunk: pd.Series):
    """Get SABR specification from a chunk of data."""
    sabr = SABR.fit_to_fx(tau=1 / 12,
                          v_atm=chunk["v_atm"],
                          contracts={0.1: {"ms": chunk["v_10b"],
                                           "rr": chunk["v_10r"]},
                                     0.25: {"ms": chunk["v_25b"],
                                            "rr": chunk["v_25r"]}},
                          delta_conventions={"atm_def": "dns",
                                             "is_premiumadj": True,
                                             "is_forward": False},
                          **chunk[["spot", "forward", "r_counter",
                                   "r_base"]])
    return sabr


def mf_prob_estimator(chunk: pd.Series, thresh=85):
    """Estimate risk-neutral probability of S > `thresh`."""
    sabr = sabr_getter(chunk)

    # get rnd
    rnd = sabr.get_rnd(**chunk[["spot", "forward", "r_counter", "r_base"]])

    # integrate
    x = np.arange(thresh, 200, 1e-04)
    res = simps(rnd(x), x)

    return res


def mf_var_estimator(chunk: pd.Series):
    """
    """
    sabr = sabr_getter(chunk)

    res = sabr.get_mfivariance(forward=chunk["forward"],
                               r_counter=chunk["r_counter"])

    return res


def estimate_mfiv(data) -> pd.Series:
    """Estimate MFIV.

    Assumes maturity of options and forwards to be 1/12.

    Parameters
    ----------
    data : pd.DataFrame
    """
    n_cores = cpu_count()

    # function to apply in parallel
    def apply_parallel(grp, func):
        with Pool(n_cores) as p:
            res_ = p.map(func, [group for name, group in grp])

        return res_

    res = apply_parallel(data.iterrows(), mf_var_estimator)
    res = pd.Series(res, index=data.index)

    return res


def estimate_probability(data, parallelize=False):
    """
    """
    if parallelize:
        n_cores = cpu_count()

        # function to apply in parallel
        def apply_parallel(grp, func):
            with Pool(n_cores) as p:
                res_ = p.map(func, [group for name, group in grp])

            return res_

        res = apply_parallel(data.iterrows(), mf_prob_estimator)
        res = pd.Series(res, index=data.index)

    else:
        res = dict()
        for dt, dt_grp in tqdm(data.iterrows()):
            res[dt] = mf_var_estimator(dt_grp)
        res = pd.Series(res)

    return res


def estimate_probability_multiple_levels(data) -> pd.DataFrame:
    """Estimate probability of invasion under different assumptions.

    Assumes maturity of options and forwards to be 1/12.

    Parameters
    ----------
    data : pd.DataFrame
        indexed by date
    """
    levels = [85, 100]
    n_cores = cpu_count()

    # cartesian prod of rows and levels
    itr = product([row for _, row in data.iterrows()], levels)

    # apply with a level for the second argument
    with Pool(n_cores) as p:
        ret_list = p.starmap(mf_prob_estimator, itr)

    # concat, create index
    res = pd.Series(
        ret_list,
        index=pd.MultiIndex.from_product(
            [[t for t, _ in data.iterrows()], levels],
            names=["date", "threshold"])
    ).unstack()

    return res
