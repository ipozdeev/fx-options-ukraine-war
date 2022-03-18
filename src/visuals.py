import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import lines as mlines
from matplotlib import dates as mdates

from .setup import *
from .datafeed_.downstream import get_timeline

palette = plt.rcParams['axes.prop_cycle'].by_key()['color']


def plot_spot(spot: pd.Series) -> plt.Figure:
    """Plot spot exchange rate."""
    to_plot = spot \
        .resample("1T").asfreq() \
        .rename("usdrub")
    dt_t = get_timeline().index[0]

    # canvas
    fig, ax = plt.subplots(1, 2, sharey=True, figsize=(8, 4))

    # labels
    ax[0].set_title("feb 15th - 28th")
    ax[0].set_ylabel("usdrub")
    ax[1].set_title("feb 24th")

    # lines
    to_plot.loc["2022-02-15":].plot(ax=ax[0])
    to_plot.loc["2022-02-23 18:00":"2022-02-24"].plot(ax=ax[1])
    for ax_ in ax:
        ax_.axvline(x=dt_t, color=palette[2], label="announcement", alpha=0.5)

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0], label="spot rate"),
        mlines.Line2D([], [], color=palette[2], label="announcement")
    ]
    ax[1].legend(handles=leg_handles)

    fig.tight_layout()

    return fig


def plot_rates(rates: pd.DataFrame) -> plt.Figure:
    """Plot interest rates.

    Parameters
    ----------
    rates : pd.DataFrame
        indexed by datetime, with columns 'rf' and 'div_yield'
    """
    to_plot = rates.resample("1T").asfreq()

    # canvas
    fig, ax_l = plt.subplots()
    ax_r = ax_l.twinx()

    # lines
    to_plot["rf"].plot(ax=ax_l, color=palette[0])
    to_plot["div_yield"].plot(ax=ax_r, color=palette[2])

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0], label="rub(rf), left axis"),
        mlines.Line2D([], [], color=palette[2],
                      label="usd(div_yield), right axis")
    ]
    ax_l.legend(handles=leg_handles, loc="upper left")

    # grid
    ax_l.grid(False)
    ax_r.grid(False)

    # labels
    ax_l.set_xlabel("", visible=False)
    ax_l.set_ylabel("rub")
    ax_r.set_ylabel("usd")

    return fig


def plot_invasion_probability(prob: pd.Series, show_invasion: bool = False) \
        -> plt.Figure:
    """Plot prob of invasion from 01/01/2022 up to 02/24."""

    # canvas
    fig, ax = plt.subplots(figsize=(8, 4))

    # lines
    prob.plot(ax=ax, linestyle="none", marker=".")

    if show_invasion:
        dt_t = get_timeline().index[0]
        ax.axvline(x=dt_t, color=palette[2], label="announcement", alpha=0.5)

    # labels
    ax.set_ylabel(r"$P[S > s]$")
    ax.set_xlabel("", visible=False)

    # legend
    leg_handles = [
        mlines.Line2D([], [], color=palette[0], label=r"$P[S>s]$"),
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
    dt_t = get_timeline().index[0]

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
