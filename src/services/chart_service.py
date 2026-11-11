import io
from typing import List, Dict, Any, Optional
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # Headless mode for non-interactive environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_pricing_chart(
    keyword: str,
    scope_label: str,
    records: List[Dict[str, Any]],
    stats: Dict[str, Any],
    save_path: Optional[str] = None
) -> bytes:
    """
    Generates a high-quality visualization chart for keyword pricing:
    - Top panel: Price timeline with observations, median and mean benchmarks,
                 and highlighted Lowest Price callout.
    - Bottom panel: Price distribution histogram with median, mean, and lowest price markers.
    
    Returns PNG image bytes.
    """
    if not records:
        raise ValueError("Cannot generate chart with empty records list.")

    # Sort records chronologically
    sorted_records = sorted(records, key=lambda r: r["timestamp"])
    timestamps = [r["timestamp"] for r in sorted_records]
    prices = [r["price"] for r in sorted_records]

    mean_val = stats.get("mean", 0.0)
    median_val = stats.get("median", 0.0)
    min_val = stats.get("min", 0.0)
    max_val = stats.get("max", 0.0)

    # Style configuration
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.5), gridspec_kw={"height_ratios": [1.8, 1.2]})
    fig.patch.set_facecolor("#FAFAFC")

    # ----------------- PANEL 1: Price Timeline -----------------
    ax1.set_facecolor("#FFFFFF")
    ax1.plot(timestamps, prices, color="#4C6EF5", alpha=0.45, linestyle="-", linewidth=1.5, zorder=1)
    ax1.scatter(
        timestamps, prices,
        color="#364FC7",
        alpha=0.85,
        s=48,
        edgecolors="white",
        linewidth=0.8,
        zorder=3,
        label=f"Offers (n={len(prices)})"
    )

    # Benchmark lines
    ax1.axhline(
        median_val,
        color="#2B8A3E",
        linestyle="--",
        linewidth=1.8,
        label=f"Median: R$ {median_val:,.2f}"
    )
    ax1.axhline(
        mean_val,
        color="#E8590C",
        linestyle=":",
        linewidth=1.6,
        label=f"Mean: R$ {mean_val:,.2f}"
    )
    ax1.axhline(
        min_val,
        color="#D6336C",
        linestyle="-.",
        linewidth=1.6,
        label=f"Lowest: R$ {min_val:,.2f}"
    )

    # Highlight lowest price point with star marker and callout annotation
    min_record = stats.get("cheapest_record", min(sorted_records, key=lambda r: r["price"]))
    ax1.scatter(
        [min_record["timestamp"]],
        [min_record["price"]],
        color="#D6336C",
        s=150,
        marker="*",
        zorder=5
    )

    min_date_fmt = min_record["timestamp"].strftime("%d/%m")
    ax1.annotate(
        f"Lowest Price\nR$ {min_val:,.2f} ({min_date_fmt})",
        xy=(min_record["timestamp"], min_val),
        xytext=(20, 25),
        textcoords="offset points",
        arrowprops=dict(arrowstyle="->", color="#D6336C", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.4", fc="#FFF0F6", ec="#D6336C", lw=1.2),
        fontsize=9,
        fontweight="bold",
        color="#A61E4D",
        zorder=6
    )

    ax1.set_title(
        f"Price History & Trends: \"{keyword.upper()}\" ({scope_label.upper()})",
        fontsize=14,
        fontweight="bold",
        pad=12,
        color="#212529"
    )
    ax1.set_ylabel("Price (R$)", fontsize=11, fontweight="bold", color="#343A40")
    ax1.yaxis.set_major_formatter("R$ {x:,.0f}")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M" if len(timestamps) < 20 else "%d/%m"))
    plt.setp(ax1.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    ax1.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # ----------------- PANEL 2: Distribution -----------------
    ax2.set_facecolor("#FFFFFF")
    bins = min(20, max(5, len(set(prices))))
    ax2.hist(
        prices,
        bins=bins,
        color="#748FFC",
        edgecolor="white",
        alpha=0.75,
        density=False
    )

    ax2.axvline(median_val, color="#2B8A3E", linestyle="--", linewidth=1.8, label="Median")
    ax2.axvline(mean_val, color="#E8590C", linestyle=":", linewidth=1.6, label="Mean")
    ax2.axvline(min_val, color="#D6336C", linestyle="-.", linewidth=1.6, label=f"Lowest: R$ {min_val:,.2f}")

    ax2.set_title("Price Distribution & Frequency", fontsize=12, fontweight="bold", pad=8, color="#212529")
    ax2.set_xlabel("Price (R$)", fontsize=11, fontweight="bold", color="#343A40")
    ax2.set_ylabel("Frequency", fontsize=11, fontweight="bold", color="#343A40")
    ax2.xaxis.set_major_formatter("R$ {x:,.0f}")
    ax2.legend(loc="upper right", framealpha=0.9, fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    chart_bytes = buf.getvalue()

    if save_path:
        with open(save_path, "wb") as f:
            f.write(chart_bytes)

    return chart_bytes
