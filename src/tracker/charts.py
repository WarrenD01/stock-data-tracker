from __future__ import annotations

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from tracker.prices import TickerSummary


def render_ticker_chart_png(summary: TickerSummary) -> bytes:
    """Render a PNG line chart of stored closes for a tracked ticker."""
    fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=150)

    dates = summary.history_dates
    closes = [float(c) for c in summary.history_closes]

    line_color = "#16a34a" if len(closes) < 2 or closes[-1] >= closes[0] else "#dc2626"
    ax.plot(dates, closes, marker="o", linewidth=2, color=line_color)

    ax.set_title(f"{summary.symbol} — Closing Price Since Added", fontsize=12, fontweight="bold")
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Close Price (USD)", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.4)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.read()