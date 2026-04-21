import csv
import math
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "ev_market_master.csv"
README_PATH = BASE_DIR / "README.md"

SVG_PATH = BASE_DIR / "final_project_main_figure.svg"

TITLE = "EV Adoption, Charging Buildout, and Consumer Interest Across Four Markets"
SUBTITLE = (
    "Monthly trends for France, India, the Netherlands, and the United Kingdom, "
    "using the merged market file described in the dataset README."
)


def read_readme_sources():
    text = README_PATH.read_text(encoding="utf-8")
    sources = []
    in_sources = False
    for line in text.splitlines():
        if line.strip() == "## Sources":
            in_sources = True
            continue
        if in_sources:
            if line.startswith("## "):
                break
            if line.strip().startswith("- "):
                sources.append(line.strip()[2:])
    return sources


def to_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value == "":
        return None
    return float(value)


def load_data():
    by_country = defaultdict(list)
    with DATA_PATH.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["brand"] != "All":
                continue
            row["units_sold"] = to_float(row["units_sold"])
            row["total_chargers_cumulative"] = to_float(row["total_chargers_cumulative"])
            row["trend_electric_vehicle"] = to_float(row["trend_electric_vehicle"])
            row["gasoline_price_usd_per_liter"] = to_float(row["gasoline_price_usd_per_liter"])
            by_country[row["country"]].append(row)

    for country in by_country:
        by_country[country].sort(key=lambda r: r["date"])
    return dict(sorted(by_country.items()))


def corr(xs, ys):
    if not xs or not ys or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / len(xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys) / len(ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs) / (sx * sy)


def index_series(values):
    first = None
    indexed = []
    for value in values:
        if value is not None and first is None and value != 0:
            first = value
        if value is None or first in (None, 0):
            indexed.append(None)
        else:
            indexed.append(value / first * 100.0)
    return indexed


def build_summary(by_country):
    countries = []
    for country, rows in by_country.items():
        sales = [r["units_sold"] for r in rows if r["units_sold"] is not None]
        chargers = [r["total_chargers_cumulative"] for r in rows if r["total_chargers_cumulative"] is not None]
        trends = [r["trend_electric_vehicle"] for r in rows if r["trend_electric_vehicle"] is not None]
        gas = [r["gasoline_price_usd_per_liter"] for r in rows if r["gasoline_price_usd_per_liter"] is not None]

        sales_xs, chargers_xs, trends_xs, gas_xs = [], [], [], []
        sales_for_chargers, sales_for_trends, sales_for_gas = [], [], []

        for row in rows:
            if row["units_sold"] is not None and row["total_chargers_cumulative"] is not None:
                sales_for_chargers.append(row["units_sold"])
                chargers_xs.append(row["total_chargers_cumulative"])
            if row["units_sold"] is not None and row["trend_electric_vehicle"] is not None:
                sales_for_trends.append(row["units_sold"])
                trends_xs.append(row["trend_electric_vehicle"])
            if row["units_sold"] is not None and row["gasoline_price_usd_per_liter"] is not None:
                sales_for_gas.append(row["units_sold"])
                gas_xs.append(row["gasoline_price_usd_per_liter"])

        start = rows[0]
        end = rows[-1]
        peak = max(rows, key=lambda r: r["units_sold"] if r["units_sold"] is not None else -1)

        countries.append(
            {
                "country": country,
                "date_range": [start["date"], end["date"]],
                "start_units_sold": start["units_sold"],
                "end_units_sold": end["units_sold"],
                "sales_growth_multiple": round(end["units_sold"] / start["units_sold"], 2),
                "start_total_chargers": start["total_chargers_cumulative"],
                "end_total_chargers": end["total_chargers_cumulative"],
                "peak_sales_month": peak["date"],
                "peak_units_sold": peak["units_sold"],
                "end_search_interest": end["trend_electric_vehicle"],
                "end_gasoline_price": end["gasoline_price_usd_per_liter"],
                "sales_chargers_correlation": round(corr(chargers_xs, sales_for_chargers), 3),
                "sales_search_correlation": round(corr(trends_xs, sales_for_trends), 3),
                "sales_gasoline_correlation": round(corr(gas_xs, sales_for_gas), 3),
                "observations": len(rows),
            }
        )
    return {"title": TITLE, "subtitle": SUBTITLE, "countries": countries, "sources": read_readme_sources()}


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_num(value):
    if value is None:
        return "N/A"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def round_up(value, base=100):
    if value <= 0:
        return base
    return int(math.ceil(value / base) * base)


def polyline(points, color, width=4, dash=None):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points if x is not None and y is not None)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<polyline fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linejoin="round" stroke-linecap="round"{dash_attr} points="{pts}" />'
    )


def label_box(x, y, text, color, anchor="start"):
    text = esc(text)
    approx_width = max(34, len(text) * 9 + 12)
    if anchor == "end":
        rect_x = x - approx_width
        text_x = x - 8
        text_anchor = "end"
    else:
        rect_x = x
        text_x = x + 8
        text_anchor = "start"
    rect_y = y - 16
    return (
        f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{approx_width:.1f}" height="24" rx="8" '
        f'fill="#ffffff" fill-opacity="0.92" stroke="{color}" stroke-opacity="0.18" />'
        f'<text x="{text_x:.1f}" y="{y + 1:.1f}" text-anchor="{text_anchor}" font-size="12" '
        f'font-family="Helvetica, Arial, sans-serif" font-weight="700" fill="{color}">{text}</text>'
    )


def build_svg(by_country):
    width = 1600
    height = 1220
    panel_w = 680
    panel_h = 360
    lefts = [100, 820]
    tops = [220, 650]
    colors = {
        "sales": "#1f4e79",
        "chargers": "#d97706",
        "trend": "#2b8a3e",
        "grid": "#d9dde3",
        "axis": "#475467",
        "text": "#101828",
        "muted": "#667085",
        "panel_bg": "#f8fafc",
    }

    countries = list(by_country.keys())
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff" />',
        f'<text x="100" y="70" font-size="34" font-family="Helvetica, Arial, sans-serif" fill="{colors["text"]}" font-weight="700">{esc(TITLE)}</text>',
        f'<text x="100" y="108" font-size="18" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">{esc(SUBTITLE)}</text>',
        f'<text x="100" y="142" font-size="14" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">Blue = indexed EV sales (2019-01 = 100), orange = indexed public chargers (2019-01 = 100), green dashed = Google Trends score for "electric vehicle" (0-100).</text>',
    ]

    legend_x = 100
    legend_y = 170
    legend_items = [
        ("sales", "Indexed EV sales"),
        ("chargers", "Indexed charging infrastructure"),
        ("trend", 'Search interest: "electric vehicle"'),
    ]
    for i, (key, label) in enumerate(legend_items):
        x = legend_x + i * 360
        if key == "trend":
            parts.append(
                f'<line x1="{x}" y1="{legend_y}" x2="{x + 50}" y2="{legend_y}" stroke="{colors[key]}" stroke-width="5" stroke-dasharray="10 8" />'
            )
        else:
            parts.append(
                f'<line x1="{x}" y1="{legend_y}" x2="{x + 50}" y2="{legend_y}" stroke="{colors[key]}" stroke-width="5" />'
            )
        parts.append(
            f'<text x="{x + 62}" y="{legend_y + 6}" font-size="16" font-family="Helvetica, Arial, sans-serif" fill="{colors["text"]}">{esc(label)}</text>'
        )

    for idx, country in enumerate(countries):
        rows = by_country[country]
        left = lefts[idx % 2]
        top = tops[idx // 2]
        right = left + panel_w
        bottom = top + panel_h
        plot_left = left + 58
        plot_right = right - 20
        plot_top = top + 36
        plot_bottom = bottom - 58
        plot_w = plot_right - plot_left
        plot_h = plot_bottom - plot_top

        sales_idx = index_series([r["units_sold"] for r in rows])
        charger_idx = index_series([r["total_chargers_cumulative"] for r in rows])
        trend_vals = [r["trend_electric_vehicle"] for r in rows]

        left_max = max(v for v in sales_idx + charger_idx if v is not None)
        left_max = round_up(left_max, 100 if left_max < 1000 else 250)
        right_max = 100

        def x_pos(i):
            if len(rows) == 1:
                return plot_left
            return plot_left + i * (plot_w / (len(rows) - 1))

        def y_left(v):
            return plot_bottom - (v / left_max) * plot_h

        def y_right(v):
            return plot_bottom - (v / right_max) * plot_h

        parts.append(
            f'<rect x="{left}" y="{top}" width="{panel_w}" height="{panel_h}" rx="18" fill="{colors["panel_bg"]}" stroke="#e4e7ec" />'
        )
        parts.append(
            f'<text x="{left + 24}" y="{top + 24}" font-size="24" font-family="Helvetica, Arial, sans-serif" fill="{colors["text"]}" font-weight="700">{esc(country)}</text>'
        )

        for tick in range(0, 5):
            y = plot_top + tick * (plot_h / 4)
            val = left_max - tick * (left_max / 4)
            parts.append(f'<line x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}" stroke="{colors["grid"]}" stroke-width="1" />')
            parts.append(
                f'<text x="{plot_left - 10}" y="{y + 5:.1f}" text-anchor="end" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">{esc(fmt_num(val))}</text>'
            )
            right_val = right_max - tick * (right_max / 4)
            parts.append(
                f'<text x="{plot_right + 8}" y="{y + 5:.1f}" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">{esc(fmt_num(right_val))}</text>'
            )

        year_positions = list(range(0, len(rows), 12))
        years = [rows[i]["date"][:4] for i in year_positions]
        for pos, year in zip(year_positions, years):
            x = x_pos(pos)
            parts.append(f'<line x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" y2="{plot_bottom}" stroke="#eef2f6" stroke-width="1" />')
            parts.append(
                f'<text x="{x:.1f}" y="{plot_bottom + 24}" text-anchor="middle" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">{esc(year)}</text>'
            )

        sales_points = [(x_pos(i), y_left(v)) for i, v in enumerate(sales_idx) if v is not None]
        charger_points = [(x_pos(i), y_left(v)) for i, v in enumerate(charger_idx) if v is not None]
        trend_points = [(x_pos(i), y_right(v)) for i, v in enumerate(trend_vals) if v is not None]

        parts.append(polyline(charger_points, colors["chargers"], width=4))
        parts.append(polyline(sales_points, colors["sales"], width=5))
        parts.append(polyline(trend_points, colors["trend"], width=4, dash="10 8"))

        # end labels
        last_sales = next(v for v in reversed(sales_idx) if v is not None)
        last_chargers = next(v for v in reversed(charger_idx) if v is not None)
        last_trend = next(v for v in reversed(trend_vals) if v is not None)
        parts.append(
            f'<circle cx="{sales_points[-1][0]:.1f}" cy="{sales_points[-1][1]:.1f}" r="4.5" fill="{colors["sales"]}" />'
        )
        parts.append(
            f'<circle cx="{charger_points[-1][0]:.1f}" cy="{charger_points[-1][1]:.1f}" r="4.5" fill="{colors["chargers"]}" />'
        )
        parts.append(
            f'<circle cx="{trend_points[-1][0]:.1f}" cy="{trend_points[-1][1]:.1f}" r="4.5" fill="{colors["trend"]}" />'
        )
        parts.append(
            f'<text x="{plot_left}" y="{top + 52}" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">Left axis: indexed sales/chargers</text>'
        )
        parts.append(
            f'<text x="{plot_right - 5}" y="{top + 28}" text-anchor="end" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">Right axis: Google Trends score</text>'
        )
        summary_line = (
            f'2019-01 sales {fmt_num(rows[0]["units_sold"])} → 2023-12 sales {fmt_num(rows[-1]["units_sold"])}; '
            f'chargers {fmt_num(rows[0]["total_chargers_cumulative"])} → {fmt_num(rows[-1]["total_chargers_cumulative"])}'
        )
        parts.append(
            f'<text x="{left + 24}" y="{bottom - 12}" font-size="12" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">{esc(summary_line)}</text>'
        )
        label_x = plot_right - 70
        sales_label_y = max(plot_top + 16, sales_points[-1][1] - 26)
        trend_label_y = min(plot_bottom - 8, trend_points[-1][1] - 24)
        if abs(trend_label_y - sales_label_y) < 26:
            trend_label_y = min(plot_bottom - 8, sales_label_y + 28)
        charger_label_y = max(plot_top + 18, charger_points[-1][1] + 28)
        if abs(charger_label_y - trend_label_y) < 24:
            charger_label_y = min(plot_bottom - 8, trend_label_y + 26)
        if abs(charger_label_y - sales_label_y) < 24:
            charger_label_y = min(plot_bottom - 8, sales_label_y + 52)

        parts.append(label_box(label_x, sales_label_y, fmt_num(last_sales), colors["sales"], anchor="start"))
        parts.append(label_box(label_x, charger_label_y, fmt_num(last_chargers), colors["chargers"], anchor="start"))
        parts.append(label_box(label_x, trend_label_y, fmt_num(last_trend), colors["trend"], anchor="start"))

    parts.append(
        f'<text x="100" y="1175" font-size="13" font-family="Helvetica, Arial, sans-serif" fill="{colors["muted"]}">Figure built in Python from ev_market_master.csv. Data coverage and source list were taken from the dataset README and its cited sources.</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    by_country = load_data()
    SVG_PATH.write_text(build_svg(by_country), encoding="utf-8")

    print("Created file:")
    print(f"- {SVG_PATH.name}")


if __name__ == "__main__":
    main()
