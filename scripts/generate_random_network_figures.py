#!/usr/bin/env python3
"""Build the static figures used in Random Networks and Connectivity.

All data follow the G(n, p) model or its stated formulas. No course figures or
data are used. Samples use Python's local Random instance, fixed seeds, and
lexicographic pairs, so the output does not depend on global random state.
Run this script to rebuild the SVGs. Quarto only needs the checked-in images.
"""

from __future__ import annotations

import argparse
import html
import itertools
import math
from pathlib import Path
import random


BLUE = "#2563eb"
PURPLE = "#7c3aed"
ORANGE = "#b45309"
INK = "#0f172a"
MUTED = "#475569"
GRID = "#cbd5e1"
BACKGROUND = "#f8fafc"


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer greater than or equal to {minimum}")


def _probability(p: float) -> None:
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("p must be a finite probability between 0 and 1")


def sample_edges(n: int, p: float, seed: int) -> list[tuple[int, int]]:
    """Sample 1-based, sorted edges, with one independent draw for each pair."""
    _integer(n, "n", 2)
    _probability(p)
    rng = random.Random(seed)
    return [pair for pair in itertools.combinations(range(1, n + 1), 2) if rng.random() < p]


def binomial_pmf(trials: int, p: float, k: int) -> float:
    """Return P(Bin(trials, p) = k), including the degenerate endpoints."""
    _integer(trials, "trials")
    _probability(p)
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be an integer")
    if k < 0 or k > trials:
        return 0.0
    if p == 0:
        return float(k == 0)
    if p == 1:
        return float(k == trials)
    return math.exp(
        math.lgamma(trials + 1) - math.lgamma(k + 1) - math.lgamma(trials - k + 1)
        + k * math.log(p) + (trials - k) * math.log1p(-p)
    )


def poisson_pmf(mean: float, k: int) -> float:
    """Return P(Poisson(mean) = k)."""
    if isinstance(mean, bool) or not isinstance(mean, (int, float)) or not math.isfinite(mean) or mean < 0:
        raise ValueError("mean must be finite and nonnegative")
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be an integer")
    if k < 0:
        return 0.0
    if mean == 0:
        return float(k == 0)
    return math.exp(-mean + k * math.log(mean) - math.lgamma(k + 1))


def expected_isolates(n: int, p: float) -> float:
    """Return the exact expected number of isolated nodes in G(n, p)."""
    _integer(n, "n", 2)
    _probability(p)
    return n * (1 - p) ** (n - 1)


def isolated_variance(n: int, p: float) -> float:
    """Return the exact variance, including the shared-edge covariance term."""
    _integer(n, "n", 2)
    _probability(p)
    a = (1 - p) ** (n - 1)
    return n * a * (1 - a) + n * (n - 1) * p * (1 - p) ** (2 * n - 3)


def _text(x: float, y: float, text: str, size: int = 20, anchor: str = "start", color: str = INK, extra: str = "") -> str:
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{html.escape(text)}</text>'


def _line(x1: float, y1: float, x2: float, y2: float, color: str = GRID, width: float = 1, extra: str = "") -> str:
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" {extra}/>'


def _document(title: str, description: str, body: list[str], height: int, metadata: str) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 {height}" width="640" height="{height}" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{html.escape(title)}</title>',
        f'  <desc id="desc">{html.escape(description)}</desc>',
        f'  <metadata>{html.escape(metadata)}</metadata>',
        f'  <rect width="640" height="{height}" rx="16" fill="{BACKGROUND}"/>',
        '  <g font-family="Arial, Helvetica, sans-serif">',
        *["    " + item for item in body],
        "  </g>",
        "</svg>",
        "",
    ])


def _sample_figure(seed: int, sample_number: int) -> str:
    n, p = 9, 1 / 3
    edges = sample_edges(n, p, seed)
    degrees = [sum(node in edge for edge in edges) for node in range(1, n + 1)]
    title = f"Sample {sample_number}: G(9, 1/3)"
    edge_description = ", ".join(f"{u}–{v}" for u, v in edges)
    description = (
        f"A simple undirected random graph with 9 nodes and {len(edges)} edges. "
        f"Seed {seed}. Degrees of nodes 1 through 9: {', '.join(map(str, degrees))}. "
        f"Edges: {edge_description}."
    )
    body = [
        _text(320, 38, title, 27, "middle", extra='font-weight="600"'),
        _text(320, 70, f"{len(edges)} edges · {degrees.count(0)} isolated nodes", 21, "middle", MUTED),
    ]
    positions = {
        i + 1: (320 + 175 * math.cos(-math.pi / 2 + 2 * math.pi * i / n),
                285 + 175 * math.sin(-math.pi / 2 + 2 * math.pi * i / n))
        for i in range(n)
    }
    body.append('<g stroke-linecap="round" opacity="0.78">')
    for u, v in edges:
        x1, y1 = positions[u]
        x2, y2 = positions[v]
        body.append(_line(x1, y1, x2, y2, "#64748b", 2.8, f'class="graph-edge" data-source="{u}" data-target="{v}"'))
    body.append("</g>")
    for node, (x, y) in positions.items():
        body.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="21" fill="#dbeafe" stroke="#1e40af" stroke-width="2.5" data-node="{node}" data-degree="{degrees[node - 1]}"/>')
        body.append(_text(x, y + 1, str(node), 23, "middle", "#172554", 'dominant-baseline="central" font-weight="600"'))
    body.append(_text(320, 500, f"Seed: {seed}", 18, "middle", MUTED))
    return _document(title, description, body, 520, f"G(n,p); n=9; p=1/3; seed={seed}; pairs=lexicographic; generator=random.Random")


def _legend(y: float, color: str, label: str, dash: bool = False, shape: str = "circle") -> list[str]:
    items = [_line(87, y - 6, 123, y - 6, color, 3, 'stroke-dasharray="7 5"' if dash else "")]
    if shape == "square":
        items.append(f'<rect x="101" y="{y - 10:.2f}" width="8" height="8" fill="{color}"/>')
    elif shape == "circle":
        items.append(f'<circle cx="105" cy="{y - 6:.2f}" r="4.2" fill="{color}"/>')
    items.append(_text(135, y, label, 19))
    return items


def _degree_figure() -> str:
    title = "Degrees Near a Poisson Distribution"
    body = [
        _text(320, 36, title, 25, "middle", extra='font-weight="600"'),
        _text(320, 63, "All three distributions have mean 3", 20, "middle", MUTED),
    ]
    body += _legend(91, BLUE, "Binomial(24, 3/24): n = 25")
    body += _legend(117, PURPLE, "Binomial(99, 3/99): n = 100", shape="square")
    body += _legend(143, ORANGE, "Poisson(3)", dash=True, shape="none")
    left, right, top, bottom = 85, 610, 178, 447
    x = lambda k: left + (right - left) * k / 12
    y = lambda probability: bottom - (bottom - top) * probability / 0.25
    for index in range(6):
        probability = index * 0.05
        body.append(_line(left, y(probability), right, y(probability)))
        body.append(_text(left - 10, y(probability) + 6, f"{probability:.2f}", 18, "end", MUTED))
    for k in range(0, 13, 2):
        body.append(_line(x(k), bottom, x(k), bottom + 6, MUTED))
        body.append(_text(x(k), bottom + 26, str(k), 18, "middle", MUTED))
    body += [_line(left, top, left, bottom, MUTED, 1.4), _line(left, bottom, right, bottom, MUTED, 1.4)]
    for color, distribution, dash, shape in [
        (BLUE, lambda k: binomial_pmf(24, 3 / 24, k), False, "circle"),
        (PURPLE, lambda k: binomial_pmf(99, 3 / 99, k), False, "square"),
        (ORANGE, lambda k: poisson_pmf(3, k), True, "none"),
    ]:
        points = " ".join(f"{x(k):.2f},{y(distribution(k)):.2f}" for k in range(13))
        extra = 'stroke-dasharray="7 5"' if dash else ""
        body.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.8" stroke-linejoin="round" {extra}/>')
        for k in range(13):
            if shape == "circle":
                body.append(f'<circle cx="{x(k):.2f}" cy="{y(distribution(k)):.2f}" r="3.5" fill="{color}"/>')
            elif shape == "square":
                body.append(f'<rect x="{x(k) - 3:.2f}" y="{y(distribution(k)) - 3:.2f}" width="6" height="6" fill="{color}"/>')
    body += [
        _text(347, 501, "Number of Neighbours, k", 21, "middle"),
        _text(21, 312, "Probability", 20, "middle", extra='transform="rotate(-90 21 312)"'),
        _text(320, 532, "k = 0–12 shown; probabilities are not rescaled.", 17, "middle", MUTED),
    ]
    description = (
        "Probability mass functions for Binomial(24, 3/24), Binomial(99, 3/99), and Poisson(3). "
        "All have mean 3. The binomial curves move closer to the Poisson curve as n grows. "
        "Only degrees 0 through 12 are shown. Tail probabilities are omitted, not rescaled. "
        "Lines join discrete values to help compare them."
    )
    return _document(title, description, body, 552, "Exact PMFs; n=25,100; p=3/(n-1); Poisson mean=3; k=0..12; no renormalization")


def _isolated_figure() -> str:
    title = "Expected Number of Isolated Nodes"
    body = [
        _text(320, 36, title, 25, "middle", extra='font-weight="600"'),
        _text(320, 65, "p = c log(n) / n · Exact finite-n expectations", 19, "middle", MUTED),
    ]
    for cx, color, label, dash in [(87, BLUE, "n = 60", ""), (265, PURPLE, "n = 600", "7 4"), (445, ORANGE, "n = 6000", "2 4")]:
        body.append(_line(cx, 91, cx + 33, 91, color, 3, f'stroke-dasharray="{dash}"' if dash else ""))
        body.append(_text(cx + 42, 97, label, 18))
    left, right, top, bottom = 85, 610, 132, 438
    log_min, log_max = math.log10(0.005), math.log10(200)
    x = lambda c: left + (right - left) * (c - 0.5)
    y = lambda expectation: bottom - (bottom - top) * (math.log10(expectation) - log_min) / (log_max - log_min)
    for expectation in (0.01, 0.1, 1, 10, 100):
        body.append(_line(left, y(expectation), right, y(expectation), "#94a3b8" if expectation == 1 else GRID, 1.5 if expectation == 1 else 1, 'stroke-dasharray="5 4"' if expectation == 1 else ""))
        body.append(_text(left - 10, y(expectation) + 6, f"{expectation:g}", 18, "end", MUTED))
    body.append(_line(x(1), top, x(1), bottom, "#94a3b8", 1.5, 'stroke-dasharray="5 4"'))
    for c in (0.5, 0.75, 1, 1.25, 1.5):
        body.append(_line(x(c), bottom, x(c), bottom + 6, MUTED))
        body.append(_text(x(c), bottom + 27, f"{c:g}", 18, "middle", MUTED))
    body += [_line(left, top, left, bottom, MUTED, 1.4), _line(left, bottom, right, bottom, MUTED, 1.4)]
    for n, color, dash in [(60, BLUE, ""), (600, PURPLE, "7 4"), (6000, ORANGE, "2 4")]:
        points = []
        for index in range(201):
            c = 0.5 + index / 200
            expectation = expected_isolates(n, c * math.log(n) / n)
            points.append(f"{x(c):.2f},{y(expectation):.2f}")
        extra = f'stroke-dasharray="{dash}"' if dash else ""
        body.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" {extra}/>')
    body += [
        _text(347, 493, "c", 22, "middle", extra='font-style="italic"'),
        _text(21, 285, "Expected Count (Log Scale)", 19, "middle", extra='transform="rotate(-90 21 285)"'),
        _text(320, 527, "These curves show expectations, not probabilities.", 17, "middle", MUTED),
    ]
    description = (
        "The exact expected count n(1-p)^(n-1), with p=c log(n)/n, for n=60, 600, and 6000. "
        "The horizontal axis runs from c=0.5 to c=1.5. The vertical axis is logarithmic. "
        "Reference lines mark c=1 and expected count 1. Curves get steeper as n grows. "
        "All three values near c=1 are close to, but not exactly, 1. These are expectations, not probabilities."
    )
    return _document(title, description, body, 548, "E[X]=n(1-c log(n)/n)^(n-1); natural log; n=60,600,6000; c=0.5..1.5; 201 points; log10 vertical scale")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "notes" / "math1972-seminar" / "images")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "random-network-sample-1.svg": _sample_figure(20261020, 1),
        "random-network-sample-2.svg": _sample_figure(20261021, 2),
        "random-network-degree-poisson.svg": _degree_figure(),
        "random-network-isolated-expectation.svg": _isolated_figure(),
    }
    for name, content in figures.items():
        (args.output_dir / name).write_text(content, encoding="utf-8")
        print(name)


if __name__ == "__main__":
    main()
