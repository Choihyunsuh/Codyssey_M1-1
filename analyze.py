#!/usr/bin/env python3
"""Analyze daily KRW per USD observations and create three SVG charts.

Uses only Python's standard library. Run from this directory with:
    python analyze.py
"""

from __future__ import annotations

import csv
import html
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "DEXKOUS.csv"
IMAGE_DIR = ROOT / "images"
START = date(2021, 10, 29)
END = date(2026, 10, 29)
WINDOW = 30  # 30 available observations (roughly six trading weeks).


def load_data() -> tuple[list[tuple[date, float]], int, int]:
    """Load source rows, retain the requested date range, and omit missing values."""
    observations: list[tuple[date, float]] = []
    source_rows = 0
    missing_in_range = 0
    with INPUT.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"observation_date", "DEXKOUS"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV must contain these columns: {sorted(required)}")
        for row in reader:
            source_rows += 1
            day = date.fromisoformat(row["observation_date"].strip())
            if not START <= day <= END:
                continue
            raw_value = (row["DEXKOUS"] or "").strip()
            if not raw_value or raw_value == ".":
                missing_in_range += 1
                continue
            value = float(raw_value)
            if not math.isfinite(value):
                missing_in_range += 1
                continue
            observations.append((day, value))
    observations.sort()
    if not observations:
        raise ValueError("No valid observations found in the configured date range.")
    return observations, source_rows, missing_in_range


def moving_average(
    observations: list[tuple[date, float]], window: int
) -> list[tuple[date, float]]:
    return [
        (observations[index][0], statistics.mean(value for _, value in observations[index - window + 1 : index + 1]))
        for index in range(window - 1, len(observations))
    ]


def monthly_groups(
    observations: list[tuple[date, float]],
) -> dict[str, list[tuple[date, float]]]:
    groups: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for day, value in observations:
        groups[day.strftime("%Y-%m")].append((day, value))
    return dict(sorted(groups.items()))


def svg_header(title: str, width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,"Noto Sans KR",sans-serif;fill:#263238}.small{font-size:12px}.label{font-size:14px}.title{font-size:20px;font-weight:700}.grid{stroke:#dfe5eb;stroke-width:1}.axis{stroke:#62717d;stroke-width:1}</style>',
        f'<text x="72" y="34" class="title">{html.escape(title)}</text>',
    ]


def line_chart(
    path: Path,
    title: str,
    series: list[tuple[str, list[tuple[date, float]], str]],
    y_label: str,
    x_tick_indices: list[int],
    x_tick_labels: list[str],
    y_formatter,
) -> None:
    width, height = 1200, 680
    left, right, top, bottom = 88, 1160, 78, 570
    all_points = [point for _, data, _ in series for point in data]
    y_values = [value for _, value in all_points]
    low, high = min(y_values), max(y_values)
    pad = (high - low) * 0.08 or 1
    low -= pad
    high += pad
    # All lines share the same observation-count x axis; convert dates to an index.
    base_dates = [day for day, _ in series[0][1]]
    date_to_index = {day: index for index, day in enumerate(base_dates)}
    x_max = max(1, len(base_dates) - 1)

    def x_pos(index: int) -> float:
        return left + (right - left) * index / x_max

    def y_pos(value: float) -> float:
        return bottom - (bottom - top) * (value - low) / (high - low)

    parts = svg_header(title, width, height)
    for tick in range(6):
        value = low + (high - low) * tick / 5
        y = y_pos(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="small">{html.escape(y_formatter(value))}</text>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" class="axis"/>')
    for index, label in zip(x_tick_indices, x_tick_labels):
        x = x_pos(index)
        parts.append(f'<line x1="{x:.1f}" y1="{bottom}" x2="{x:.1f}" y2="{bottom+5}" class="axis"/>')
        parts.append(f'<text x="{x:.1f}" y="{bottom+25}" text-anchor="middle" class="small">{html.escape(label)}</text>')
    parts.append(f'<text x="22" y="{(top+bottom)/2:.1f}" transform="rotate(-90 22 {(top+bottom)/2:.1f})" text-anchor="middle" class="label">{html.escape(y_label)}</text>')
    for label, data, color in series:
        coords = []
        for day, value in data:
            index = date_to_index.get(day)
            if index is not None:
                coords.append(f'{x_pos(index):.1f},{y_pos(value):.1f}')
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(coords)}"/>')
    legend_x = left
    for label, _, color in series:
        parts.append(f'<line x1="{legend_x}" y1="625" x2="{legend_x+26}" y2="625" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{legend_x+34}" y="630" class="small">{html.escape(label)}</text>')
        legend_x += 210
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def monthly_return_chart(path: Path, returns: list[tuple[str, float]]) -> None:
    width, height = 1200, 680
    left, right, top, bottom = 88, 1160, 78, 570
    low = min(value for _, value in returns)
    high = max(value for _, value in returns)
    extent = max(abs(low), abs(high)) * 1.15 or 1

    def y_pos(value: float) -> float:
        return bottom - (bottom - top) * (value + extent) / (2 * extent)

    parts = svg_header("월말 환율 기준 월간 변화율", width, height)
    zero_y = y_pos(0)
    for tick in range(-4, 5, 2):
        value = extent * tick / 4
        y = y_pos(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" class="small">{value:.1f}%</text>')
    parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{right}" y2="{zero_y:.1f}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" class="axis"/>')
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" class="axis"/>')
    slot = (right - left) / max(1, len(returns))
    bar_width = max(4, slot * 0.68)
    for index, (month, value) in enumerate(returns):
        x = left + index * slot + (slot - bar_width) / 2
        y = y_pos(value)
        color = "#277da1" if value >= 0 else "#e76f51"
        parts.append(f'<rect x="{x:.1f}" y="{min(y, zero_y):.1f}" width="{bar_width:.1f}" height="{max(1, abs(zero_y-y)):.1f}" fill="{color}"/>')
        if month.endswith("-01") or index == 0 or index == len(returns)-1:
            parts.append(f'<text x="{x+bar_width/2:.1f}" y="{bottom+24}" text-anchor="middle" class="small">{month}</text>')
    parts.append(f'<text x="22" y="{(top+bottom)/2:.1f}" transform="rotate(-90 22 {(top+bottom)/2:.1f})" text-anchor="middle" class="label">전월 말 대비 변화율(%)</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    observations, source_rows, missing = load_data()
    dates = [day for day, _ in observations]
    values = [value for _, value in observations]
    rolling = moving_average(observations, WINDOW)
    groups = monthly_groups(observations)
    month_means = [(month, statistics.mean(value for _, value in group)) for month, group in groups.items()]
    month_closes = [(month, group[-1][1]) for month, group in groups.items()]
    month_returns = [
        (month_closes[index][0], 100 * (month_closes[index][1] / month_closes[index - 1][1] - 1))
        for index in range(1, len(month_closes))
    ]

    ticks = list(range(0, len(observations), 250))
    if ticks[-1] != len(observations) - 1:
        ticks.append(len(observations) - 1)
    tick_labels = [dates[index].strftime("%Y-%m") for index in ticks]
    line_chart(
        IMAGE_DIR / "01_daily_and_moving_average.svg",
        "원/달러 환율 일별 추이와 30개 관측값 이동평균",
        [("일별 환율", observations, "#9aa6b2"), ("30개 관측값 이동평균", rolling, "#d1495b")],
        "원/달러 (원)", ticks, tick_labels, lambda value: f"{value:,.0f}",
    )

    monthly_observations = [(date.fromisoformat(month + "-01"), value) for month, value in month_means]
    month_ticks = list(range(0, len(monthly_observations), 6))
    if month_ticks[-1] != len(monthly_observations) - 1:
        month_ticks.append(len(monthly_observations) - 1)
    line_chart(
        IMAGE_DIR / "02_monthly_average.svg",
        "월별 평균 원/달러 환율",
        [("월별 평균", monthly_observations, "#277da1")],
        "원/달러 (원)", month_ticks,
        [monthly_observations[index][0].strftime("%Y-%m") for index in month_ticks],
        lambda value: f"{value:,.0f}",
    )
    monthly_return_chart(IMAGE_DIR / "03_monthly_change.svg", month_returns)

    highest = max(observations, key=lambda item: item[1])
    lowest = min(observations, key=lambda item: item[1])
    changes = [
        (observations[index][0], observations[index][1] - observations[index - 1][1],
         100 * (observations[index][1] / observations[index - 1][1] - 1))
        for index in range(1, len(observations))
    ]
    largest_rise = max(changes, key=lambda item: item[1])
    largest_fall = min(changes, key=lambda item: item[1])
    print(f"CSV rows: {source_rows}; valid observations: {len(observations)}; missing in range: {missing}")
    print(f"Coverage: {observations[0][0]} to {observations[-1][0]}")
    print(f"First/last: {values[0]:.2f} / {values[-1]:.2f} KRW per USD ({100 * (values[-1] / values[0] - 1):+.2f}%)")
    print(f"Minimum: {lowest[0]} {lowest[1]:.2f}; maximum: {highest[0]} {highest[1]:.2f}")
    print(f"Largest observed-day rise: {largest_rise[0]} {largest_rise[1]:+.2f} ({largest_rise[2]:+.2f}%)")
    print(f"Largest observed-day fall: {largest_fall[0]} {largest_fall[1]:+.2f} ({largest_fall[2]:+.2f}%)")
    print(f"Latest {WINDOW}-observation average: {rolling[-1][1]:.2f}")
    print("Created: images/01_daily_and_moving_average.svg, images/02_monthly_average.svg, images/03_monthly_change.svg")


if __name__ == "__main__":
    main()
