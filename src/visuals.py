import numpy as np
import pandas as pd
import re
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.dates import DayLocator, DateFormatter, \
    WeekdayLocator, MO, MonthLocator, HourLocator
from matplotlib.ticker import FormatStrFormatter, MultipleLocator

mpl.style.use("seaborn-v0_8-colorblind")
palette = plt.rcParams['axes.prop_cycle'].by_key()['color']


def plot_spot(spot: pd.Series, timeline: pd.Series) -> plt.Figure:
    """Plot spot exchange rate."""
    to_plot = spot.rename("usdrub")
    dt_t = timeline.index[-1]

    # canvas
    fig, ax = plt.subplots(1, 2, sharey=True, sharex=False, figsize=(8, 4))

    # labels
    # ax[0].set_title("")
    ax[0].set_ylabel("usdrub")

    # lines
    to_plot.loc["2022-02":"2022-04"].plot(ax=ax[0])
    to_plot.loc["2022-02-23 18:00":"2022-02-24"].plot(ax=ax[1])
    
    # attr common to both axes
    for _ax in ax:
        _ax.axvline(x=dt_t, color="k", label="announcement")
        _ax.set_xlabel("", visible=None)
        _ax.grid(which="both", axis="both")

    # xticks
    ax[0].xaxis.set_major_locator(MonthLocator(bymonthday=24))
    ax[0].xaxis.set_minor_locator(WeekdayLocator(byweekday=MO))
    ax[0].xaxis.set_major_formatter(DateFormatter("%b-%d"))
    ax[0].xaxis.set_minor_formatter(DateFormatter("%d"))
    ax[1].xaxis.set_major_locator(MonthLocator(bymonth=2, bymonthday=24))
    ax[1].xaxis.set_major_formatter(DateFormatter("%b-%d"))
    ax[1].xaxis.set_minor_locator(HourLocator(interval=6))
    ax[1].xaxis.set_minor_formatter(DateFormatter("%H:%M"))
    
    fig.autofmt_xdate(rotation=0, ha="center")

    # legend
    leg_handles = [
        Line2D([], [], color=palette[0], label="spot rate"),
        Line2D([], [], color="k", label="announcement")
    ]
    ax[1].legend(handles=leg_handles)
    plt.suptitle("spot usdrub around invasion", y=0.95)

    fig.tight_layout()

    return fig


def plot_rates(rates: pd.DataFrame, timeline: pd.Series) -> plt.Figure:
    """Plot interest rates.

    Parameters
    ----------
    rates : pd.DataFrame
        indexed by datetime, with columns 'r_counter' and 'r_base'
    """
    to_plot = rates.resample("1T").asfreq()

    # canvas
    fig, ax_l = plt.subplots()
    ax_r = ax_l.twinx()

    # lines
    to_plot["r_counter"].plot(ax=ax_l, color=palette[2])
    to_plot["r_base"].plot(ax=ax_r, color=palette[0])

    # legend
    leg_handles = [
        Line2D([], [], color=palette[2],
                      label="rub(counter), left axis"),
        Line2D([], [], color=palette[0],
                      label="usd(base), right axis"),
        Line2D([], [], color="k", label="announcement")
    ]
    ax_l.legend(handles=leg_handles, loc="upper left")

    # ticks, trying to align the two axes
    ax_l.set_ylim((6, 34))
    ax_l.set_yticks(np.arange(10, 35, 5))
    ax_r.set_ylim((6/100, 34/100))
    ax_r.set_yticks(np.arange(10, 35, 5)/100)

    # announcement
    dt_t = timeline.index[-1]
    ax_l.axvline(x=dt_t, color="k", label="announcement")

    # grid off bc of two axes
    ax_l.grid(which="major", axis="y")
    ax_r.grid(False)

    # title
    ax_l.set_title("interest rates ahead of announcement")

    # labels
    ax_l.set_xlabel("", visible=False)
    ax_l.set_ylabel("rub, % p.a.")
    ax_r.set_ylabel("usd, % p.a.")

    return fig


def plot_invasion_probability(prob: pd.Series, timeline) -> plt.Figure:
    """Plot prob of invasion."""
    # canvas
    fig, axs = plt.subplots(1, 2, figsize=(8, 4), sharex=False, sharey=True)

    prob.plot(ax=axs[0], linestyle="none", marker="o", markersize=1)

    for _dt in timeline.index[:-1]:
        axs[0].axvline(x=_dt, color="k", linestyle="--", alpha=0.5)

    prob.loc["2022-02-21":].plot(ax=axs[1], linestyle="none", marker="o", 
                                 markersize=1)

    axs[0].set_ylim(-0.025, axs[0].get_ylim()[-1] / 2)

    # legend
    legend_handles = [
        Line2D([0], [0], linestyle="-", color="k"),
        Line2D([0], [0], linestyle="--", color="k", alpha=0.5)
    ]
    legend_labels = [
        "invasion", "warning"
    ]
    axs[1].legend(legend_handles, legend_labels, title="event")

    # attr common to both axes
    for _ax in axs:
        _ax.set_xlabel("", visible=None)
        _ax.axvline(x=timeline.index[-1], color="k")
        _ax.grid(which="both", axis="both")
        _ax.xaxis.set_major_formatter(DateFormatter("%b-%d"))

    # xticks
    axs[0].xaxis.set_major_locator(WeekdayLocator(byweekday=MO))
    axs[1].xaxis.set_major_locator(MonthLocator(bymonth=2, bymonthday=21))
    axs[1].xaxis.set_minor_locator(DayLocator())
    axs[1].xaxis.set_minor_formatter(DateFormatter("%d"))
    fig.autofmt_xdate(rotation=0, ha="center")

    # labels, titles
    axs[0].set_ylabel("probability")
    plt.suptitle("$P_t[S_{t+1m} > " + f"{prob.name}]$", y=0.95)

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