import numpy as np
import pandas as pd
import re
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib import lines as mlines
from matplotlib import dates as mdates
from matplotlib.ticker import FormatStrFormatter

from .datafeed import get_timeline

mpl.style.use("seaborn-v0_8-colorblind")
palette = plt.rcParams['axes.prop_cycle'].by_key()['color']


def plot_spot(spot: pd.Series) -> plt.Figure:
    """Plot spot exchange rate."""
    to_plot = spot \
        .resample("1T").asfreq() \
        .rename("usdrub")
    dt_t = get_timeline().index[-1]

    # canvas
    fig, ax = plt.subplots(1, 2, sharey=True, figsize=(8, 4))

    # labels
    # ax[0].set_title("")
    ax[0].set_ylabel("usdrub")
    ax[1].set_title("feb 24th")

    # lines
    to_plot.loc["2022-01-01":"2022-02-25"].plot(ax=ax[0])
    to_plot.loc["2022-02-23 18:00":"2022-02-24"].plot(ax=ax[1])
    for ax_ in ax:
        ax_.axvline(x=dt_t, color=palette[2], label="announcement", alpha=0.5)

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0], label="spot rate"),
        mlines.Line2D([], [], color=palette[2], label="announcement")
    ]
    ax[1].legend(handles=leg_handles)

    ax[0].grid(axis="y")
    ax[1].grid(axis="y")

    fig.tight_layout()

    return fig


def plot_rates(rates: pd.DataFrame) -> plt.Figure:
    """Plot interest rates.

    Parameters
    ----------
    rates : pd.DataFrame
        indexed by datetime, with columns 'r_conuter' and 'r_base'
    """
    to_plot = rates.resample("1T").asfreq()

    # canvas
    fig, ax_l = plt.subplots()
    ax_r = ax_l.twinx()

    # lines
    to_plot["r_counter"].plot(ax=ax_l, color=palette[0])
    to_plot["r_base"].plot(ax=ax_r, color=palette[2])

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0],
                      label="rub(counter), left axis"),
        mlines.Line2D([], [], color=palette[2],
                      label="usd(base), right axis")
    ]
    ax_l.legend(handles=leg_handles, loc="upper left")

    # grid off bc of two axes
    ax_l.grid(False)
    ax_r.grid(False)

    # title
    ax_l.set_title("interest rates ahead of announcement")

    # labels
    ax_l.set_xlabel("", visible=False)
    ax_l.set_ylabel("rub, % p.a.")
    ax_r.set_ylabel("usd, % p.a.")

    return fig


def plot_invasion_probability(prob, plot_warnings=False) -> plt.Figure:
    """Plot prob of invasion from 01/01/2022 up to 02/24."""

    # canvas
    fig, ax0 = plt.subplots(figsize=(8, 4))
    ax = (ax0, ax0.twinx())

    # lines
    leg_handles = list()
    for n_, level_ in enumerate(prob.columns):
        prob[level_].plot(ax=ax[n_], linestyle="none", marker=".",
                          color=palette[n_])
        lr = {0: "left", 1: "right"}.get(n_)
        leg_handles.append(
            mlines.Line2D([], [], color=palette[n_],
                          label=f"$P[S>{level_}]$ ({lr} axis)")
        )
        ax[n_].set_ylim(-max(prob[level_])/10, max(prob[level_]) * 10/9)
        ax[n_].set_yticks(np.linspace(0, max(prob[level_]), 5))
        ax[n_].tick_params(axis='y', colors=palette[n_])
        ax[n_].yaxis.set_major_formatter(FormatStrFormatter("%.2f"))

    leg_handles += [
        mlines.Line2D([], [], color=palette[2], label="announcement"),
    ]

    timeline = get_timeline()
    ax0.axvline(x=timeline.index[0], color=palette[2], label="announcement",
                alpha=0.5)

    if plot_warnings:
        for dt_ in timeline.index[1:]:
            ax0.axvline(x=dt_, color=palette[4], alpha=0.75)
        leg_handles += [
            mlines.Line2D([], [], color=palette[4], label="warning"),
        ]

    # labels
    ax0.set_ylabel(r"$P[S > s]$")
    ax0.set_xlabel("", visible=False)

    # legend
    ax0.legend(handles=leg_handles)

    # ticks
    ax0.set_xticklabels(ax0.get_xticklabels(), rotation=0, ha="center")
    ax0.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax0.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

    if plot_warnings:
        ax0.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax0.xaxis.set_minor_formatter(mdates.DateFormatter("%d"))

    fig.tight_layout()

    return fig


def plot_mfiv(v, show_invasion=False) -> plt.Figure:
    """Plot prob of invasion from 01/01/2022 up to 02/24."""

    # canvas
    fig, ax = plt.subplots(figsize=(8, 4))

    # lines
    v.plot(ax=ax, linestyle="none", marker=".", color=palette[0])

    if show_invasion:
        dt_t = get_timeline().index[-1]
        ax.axvline(x=dt_t, color=palette[2], label="announcement", alpha=0.5)

    # labels
    ax.set_ylabel(r"$\sqrt{mfiv}$")
    ax.set_xlabel("", visible=False)

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0],
                      label="mfi vola")
    ]
    if show_invasion:
        leg_handles += [
            mlines.Line2D([], [], color=palette[2], label="announcement")
        ]
    ax.legend(handles=leg_handles)

    # ticks
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha="center")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))

    fig.tight_layout()

    return fig


def plot_invasion_probability_zoomed(prob: pd.Series) -> plt.Figure:
    """Zoom in on Fe 23-24th."""
    dt_t = get_timeline().index[-1]

    # canvas
    fig, ax = plt.subplots(figsize=(8, 4))

    # lines
    prob.loc["2022-02-23":].loc[:dt_t]\
        .plot(ax=ax, linestyle="none", marker=".")
    ax.axvline(x=dt_t, color=palette[2], label="announcement", alpha=0.5)

    # ticks
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha="center")
    # ax.set_yticks(np.arange(0.2, 0.4, 0.05))

    # labels
    ax.set_ylabel(r"$P[S > s]$")
    ax.set_xlabel("", visible=False)

    ax.xaxis.set_major_locator(mdates.DayLocator([23, 24]))
    ax.xaxis.set_minor_locator(mdates.HourLocator([0, 4, 8, 12, 16, 20]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(which="both", axis="both", visible=True)

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0], label=r"$P[S>s]$"),
        mlines.Line2D([], [], color=palette[2], label="announcement")
    ]
    ax.legend(handles=leg_handles)

    fig.tight_layout()

    return fig


# formatting frames for notebooks
def format_dataframe(df: pd.DataFrame, precision=2):
    """A little formatter helper."""
    # if index is present, just turn it into a column
    if df.index.inferred_type == 'datetime64':
        return format_dataframe(
            df.rename_axis(index="date").reset_index(),
            precision=precision
        )
    
    # recognize column with dates
    datecol = next((s for s in df.columns if re.search("[Dd]ates?", s)), "date")
    
    res = df.style\
        .format(formatter={datecol: lambda x: x.strftime("%Y-%m-%d %H:%M")},
                precision=precision)\
        .hide(axis=0)
    
    return res