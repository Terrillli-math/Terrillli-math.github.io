#!/usr/bin/env python3
"""Build the static figures for Exponential Random Graph Models.

The examples use a specified four-node graph and exact enumeration of tiny
graph spaces. No lecture figures, empirical data, R packages, or random draws
are needed. Quarto reads the generated SVGs without running this script.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import html
import itertools
import math
from pathlib import Path


BLUE = "#2563eb"
PURPLE = "#7c3aed"
ORANGE = "#b45309"
INK = "#0f172a"
MUTED = "#475569"
GRID = "#cbd5e1"
BACKGROUND = "#f8fafc"
EXAMPLE_EDGES = ((1, 2), (1, 3), (2, 3), (3, 4))
EXAMPLE_SCORES = (0, 1, 1, 2)


def graph_space(n: int):
    """Yield all simple labelled graphs as tuples of 1-based edge pairs."""
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= 6:
        raise ValueError("exact enumeration is limited to 1 <= n <= 6")
    pairs = tuple(itertools.combinations(range(1, n + 1), 2))
    for mask in range(1 << len(pairs)):
        yield tuple(edge for bit, edge in enumerate(pairs) if mask & (1 << bit))


def graph_statistics(n: int, edges) -> dict:
    """Count edges, degrees, and unordered triangles for a tiny simple graph."""
    edges = tuple(edges)
    edge_set = set(edges)
    if len(edge_set) != len(edges) or any(not 1 <= u < v <= n for u, v in edge_set):
        raise ValueError("edges must be distinct pairs with 1 <= u < v <= n")
    degrees = tuple(sum(node in edge for edge in edge_set) for node in range(1, n + 1))
    triangles = sum(
        all(edge in edge_set for edge in itertools.combinations(triple, 2))
        for triple in itertools.combinations(range(1, n + 1), 3)
    )
    return {"edges": len(edge_set), "degrees": degrees, "triangles": triangles}


def logistic(eta: float) -> float:
    """Stable inverse logit for a finite real linear predictor."""
    if not math.isfinite(eta):
        raise ValueError("eta must be finite")
    if eta >= 0:
        return 1 / (1 + math.exp(-eta))
    exp_eta = math.exp(eta)
    return exp_eta / (1 + exp_eta)


def logistic_log_likelihood(n: int, edges, scores, beta0: float, beta1: float) -> float:
    """Log mass of one graph under the additive fixed-score logistic model."""
    edges = tuple(edges)
    graph_statistics(n, edges)
    if len(scores) != n:
        raise ValueError("one fixed score is needed per node")
    edge_set = set(edges)
    terms = []
    for i, j in itertools.combinations(range(1, n + 1), 2):
        eta = beta0 + beta1 * (scores[i - 1] + scores[j - 1])
        if not math.isfinite(eta):
            raise ValueError("linear predictors must be finite")
        # log(1 + exp(eta)) evaluated without overflow.
        normalizer = max(eta, 0) + math.log1p(math.exp(-abs(eta)))
        terms.append((eta if (i, j) in edge_set else 0) - normalizer)
    return math.fsum(terms)


def edge_triangle_distribution(n: int, theta_edge: float, theta_triangle: float):
    """Return (normalizer, [(edge tuple, probability), ...]) by exact enumeration.

    This teaching helper is for small graphs and modest finite coefficients.
    It is not an ERGM fitting or large-network simulation routine.
    """
    if not all(math.isfinite(t) for t in (theta_edge, theta_triangle)):
        raise ValueError("coefficients must be finite")
    weighted = []
    for edges in graph_space(n):
        stats = graph_statistics(n, edges)
        weight = math.exp(theta_edge * stats["edges"] + theta_triangle * stats["triangles"])
        weighted.append((edges, weight))
    normalizer = math.fsum(weight for _, weight in weighted)
    return normalizer, [(edges, weight / normalizer) for edges, weight in weighted]


def triangle_distribution(n: int, p: Fraction) -> dict[int, Fraction]:
    """Exact triangle-count probabilities for G(n, p), with rational p."""
    p = Fraction(p)
    if not 0 <= p <= 1:
        raise ValueError("p must be between zero and one")
    possible = n * (n - 1) // 2
    result = {triangles: Fraction(0) for triangles in range(math.comb(n, 3) + 1)}
    for edges in graph_space(n):
        stats = graph_statistics(n, edges)
        m = stats["edges"]
        result[stats["triangles"]] += p ** m * (1 - p) ** (possible - m)
    return result


def _text(x, y, value, size=20, anchor="start", color=INK, extra=""):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" {extra}>{html.escape(str(value))}</text>'


def _line(x1, y1, x2, y2, color=GRID, width=1, extra=""):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}" {extra}/>'


def _document(title, description, body, height, metadata):
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


def _node(x, y, label, extra=""):
    return [
        f'<circle cx="{x:.2f}" cy="{y:.2f}" r="24" fill="#dbeafe" stroke="#1e40af" stroke-width="2.5" {extra}/>',
        _text(x, y + 1, label, 24, "middle", "#172554", 'dominant-baseline="central" font-weight="600"'),
    ]


def four_node_figure():
    positions = {1: (135, 165), 2: (135, 330), 3: (360, 247.5), 4: (520, 140)}
    stats = graph_statistics(4, EXAMPLE_EDGES)
    body = [
        _text(320, 38, "One Graph, Four Node Scores", 27, "middle", extra='font-weight="600"'),
        _text(320, 72, "4 edges · 1 triangle", 21, "middle", MUTED),
    ]
    for u, v in EXAMPLE_EDGES:
        body.append(_line(*positions[u], *positions[v], BLUE, 3.2, f'class="graph-edge" data-source="{u}" data-target="{v}"'))
    for node, (x, y) in positions.items():
        score = EXAMPLE_SCORES[node - 1]
        body.extend(_node(x, y, node, f'data-node="{node}" data-score="{score}" data-degree="{stats["degrees"][node - 1]}"'))
        score_x, score_y = (60, y + 7) if node == 1 else (x, y + 52)
        body.append(_text(score_x, score_y, f"x = {score}", 22, "middle", MUTED))
    body.append(_text(320, 425, "Node numbers label vertices; x is a fixed score.", 20, "middle", MUTED))
    return _document(
        "One Graph, Four Node Scores",
        "A four-node graph with edges 1-2, 1-3, 2-3, and 3-4. Node scores are 0, 1, 1, and 2. Degrees are 2, 2, 3, and 1. Nodes 1, 2, and 3 form the only triangle.",
        body, 452, "n=4; edges=12,13,23,34; x=0,1,1,2; degrees=2,2,3,1; triangles=1",
    )


def edge_toggle_figure():
    body = [
        _text(320, 38, "One Edge, Two Conditions", 26, "middle", extra='font-weight="600"'),
        _text(320, 71, "Edge term = -log(2); triangle term = log(4)", 20, "middle", MUTED),
    ]
    for panel, offset, shared, probability in [(0, 0, 0, Fraction(1, 3)), (1, 280, 1, Fraction(2, 3))]:
        body.append(f'<rect x="24" y="{95 + offset}" width="592" height="260" rx="12" fill="#eff6ff" stroke="{GRID}"/>')
        body.append(_text(320, 127 + offset, "No Shared Neighbour" if shared == 0 else "One Shared Neighbour", 23, "middle", extra='font-weight="600"'))
        positions = {1: (170, 250 + offset), 2: (320, 175 + offset), 3: (470, 250 + offset)}
        if shared:
            for u, v in ((1, 2), (2, 3)):
                body.append(_line(*positions[u], *positions[v], BLUE, 3.5, f'class="fixed-edge" data-panel="{panel}" data-source="{u}" data-target="{v}"'))
        body.append(_line(*positions[1], *positions[3], ORANGE, 3.5, f'stroke-dasharray="10 7" class="candidate-edge" data-panel="{panel}" data-source="1" data-target="3" data-probability="{probability}"'))
        for node, (x, y) in positions.items():
            body.extend(_node(x, y, node))
        body.append(_text(320, 326 + offset, f"P(edge 1-3 | rest) = {probability}", 24, "middle", ORANGE))
    body.extend([
        _line(100, 670, 150, 670, ORANGE, 3.5, 'stroke-dasharray="10 7"'),
        _text(165, 677, "Candidate edge; all other edges are fixed", 20, color=MUTED),
    ])
    return _document(
        "One Edge, Two Conditions",
        "Two three-node networks for an edge-triangle ERGM. The candidate edge 1-3 is dashed. When all other edges are absent, its conditional probability is 1/3. When edges 1-2 and 2-3 are present, adding 1-3 closes a triangle, so its conditional probability is 2/3. The coefficients are the same in both panels.",
        body, 710, "n=3; theta_edges=-log(2); theta_triangles=log(4); conditional p13=1/3 when a12=a23=0, 2/3 when a12=a23=1",
    )


def triangle_check_figure():
    probabilities = triangle_distribution(4, Fraction(2, 3))
    body = [
        _text(320, 38, "Checking Triangles under G(4, 2/3)", 26, "middle", extra='font-weight="600"'),
        _text(320, 71, "Exact probabilities from all 64 labelled graphs", 20, "middle", MUTED),
    ]
    left, right, top, bottom = 85, 608, 140, 414
    x = lambda t: 140 + t * 102
    y = lambda p: bottom - (bottom - top) * float(p) / 0.4
    for tick in range(5):
        probability = tick / 10
        body.append(_line(left, y(probability), right, y(probability)))
        body.append(_text(left - 10, y(probability) + 6, f"{probability:.1f}", 18, "end", MUTED))
    for t, probability in probabilities.items():
        color = PURPLE if t == 1 else BLUE
        body.append(f'<rect x="{x(t)-29:.2f}" y="{y(probability):.2f}" width="58" height="{bottom-y(probability):.2f}" fill="{color}" rx="3" class="probability-bar" data-triangles="{t}" data-probability="{probability}"/>')
        body.append(_text(x(t), y(probability) - 12, f"{float(probability):.3f}", 19, "middle", color))
        body.append(_text(x(t), bottom + 27, t, 20, "middle", MUTED))
    body.extend([
        _line(left, top, left, bottom, MUTED, 1.4),
        _line(left, bottom, right, bottom, MUTED, 1.4),
        _text(347, 486, "Number of Triangles", 22, "middle"),
        _text(23, 280, "Probability", 21, "middle", extra='transform="rotate(-90 23 280)"'),
        f'<rect x="145" y="518" width="18" height="18" rx="3" fill="{PURPLE}"/>',
        _text(176, 534, "Observed graph: 1 triangle", 21, color=PURPLE),
        _text(320, 575, "p = 2/3 is fitted from the observed edge count.", 20, "middle", MUTED),
    ])
    description = (
        "The exact triangle-count distribution in G(4, 2/3). "
        + " ".join(f"P(T={t})={probability}." for t, probability in probabilities.items())
        + " The observed four-node graph has one triangle; that count is highlighted. This is an exact distribution, not a simulation or a probability that the model is true."
    )
    return _document(
        "Checking Triangles under G(4, 2/3)", description, body, 603,
        "n=4; p=2/3; all 64 labelled graphs enumerated; exact rational masses; observed m=4 and t=1; no parameter-uncertainty adjustment",
    )


def generate(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, svg in {
        "ergm-four-nodes.svg": four_node_figure(),
        "ergm-edge-toggle.svg": edge_toggle_figure(),
        "ergm-triangle-check.svg": triangle_check_figure(),
    }.items():
        (output_dir / filename).write_text(svg, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "notes/math1972-seminar/images")
    args = parser.parse_args()
    generate(args.output_dir)


if __name__ == "__main__":
    main()
