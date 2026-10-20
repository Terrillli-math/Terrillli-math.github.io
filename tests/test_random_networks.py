"""Independent checks for the random-network examples and static figures.

The graph calculations below enumerate labelled graphs. They do not reuse the
generator's probability formulas, and they never read the source note vault.
"""

from fractions import Fraction
import importlib.util
import itertools
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "scripts/generate_random_network_figures.py"
SPEC = importlib.util.spec_from_file_location("random_network_figures", SCRIPT)
FIGURES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FIGURES
SPEC.loader.exec_module(FIGURES)

SVG_NAMES = {
    "random-network-sample-1.svg",
    "random-network-sample-2.svg",
    "random-network-degree-poisson.svg",
    "random-network-isolated-expectation.svg",
}
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def enumerate_moments(n, p):
    """Compute weighted moments directly over all 2^(n choose 2) graphs."""
    possible_edges = list(itertools.combinations(range(n), 2))
    moments = {
        name: Fraction(0)
        for name in ("weight", "isolates", "isolates_squared", "pair_isolated",
                     "degree_0", "degree_1", "degree_product")
    }
    for mask in range(1 << len(possible_edges)):
        degrees = [0] * n
        edge_count = 0
        for bit, (i, j) in enumerate(possible_edges):
            if mask & (1 << bit):
                degrees[i] += 1
                degrees[j] += 1
                edge_count += 1
        weight = p ** edge_count * (1 - p) ** (len(possible_edges) - edge_count)
        isolates = degrees.count(0)
        values = {
            "weight": 1,
            "isolates": isolates,
            "isolates_squared": isolates * isolates,
            "pair_isolated": int(degrees[0] == degrees[1] == 0),
            "degree_0": degrees[0],
            "degree_1": degrees[1],
            "degree_product": degrees[0] * degrees[1],
        }
        for name, value in values.items():
            moments[name] += weight * value
    return moments


class RandomNetworkProbabilityTests(unittest.TestCase):
    def test_isolation_moments_and_shared_edge_covariance_by_enumeration(self):
        n = 4
        for p in (Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)):
            with self.subTest(p=p):
                moments = enumerate_moments(n, p)
                self.assertEqual(moments["weight"], 1)
                mean = moments["isolates"]
                variance = moments["isolates_squared"] - mean ** 2
                self.assertAlmostEqual(FIGURES.expected_isolates(n, float(p)), float(mean))
                self.assertAlmostEqual(FIGURES.isolated_variance(n, float(p)), float(variance))

                # Two isolation events forbid 2(n - 1) - 1 distinct edges.
                pair = moments["pair_isolated"]
                self.assertEqual(pair, (1 - p) ** (2 * n - 3))
                indicator_mean = mean / n
                covariance = pair - indicator_mean ** 2
                self.assertEqual(covariance, p * (1 - p) ** (2 * n - 3))
                self.assertEqual(
                    variance,
                    n * indicator_mean * (1 - indicator_mean) + n * (n - 1) * covariance,
                )

                # Degrees are not independent: their common edge has variance p(1-p).
                degree_covariance = (
                    moments["degree_product"] - moments["degree_0"] * moments["degree_1"]
                )
                self.assertEqual(degree_covariance, p * (1 - p))

    def test_nine_vertex_exact_values(self):
        n, p = 9, Fraction(1, 3)
        edge_mean = math.comb(n, 2) * p
        edge_variance = math.comb(n, 2) * p * (1 - p)
        degree_mean = (n - 1) * p
        degree_variance = (n - 1) * p * (1 - p)
        isolate_mean = n * (1 - p) ** (n - 1)
        isolate_variance = (
            n * (1 - p) ** (n - 1) * (1 - (1 - p) ** (n - 1))
            + n * (n - 1) * p * (1 - p) ** (2 * n - 3)
        )
        self.assertEqual(edge_mean, 12)
        self.assertEqual(edge_variance, 8)
        self.assertEqual(degree_mean, Fraction(8, 3))
        self.assertEqual(degree_variance, Fraction(16, 9))
        self.assertEqual(isolate_mean, Fraction(256, 729))
        self.assertEqual(isolate_variance, Fraction(625408, 1594323))
        self.assertAlmostEqual(FIGURES.expected_isolates(n, float(p)), float(isolate_mean))
        self.assertAlmostEqual(FIGURES.isolated_variance(n, float(p)), float(isolate_variance))

    def test_seeded_graphs_are_ordered_reproducible_and_have_no_isolates(self):
        for seed, expected_count in ((20261020, 16), (20261021, 15)):
            with self.subTest(seed=seed):
                generator = random.Random(seed)
                expected_edges = [
                    edge for edge in itertools.combinations(range(1, 10), 2)
                    if generator.random() < 1 / 3
                ]
                edges = FIGURES.sample_edges(9, 1 / 3, seed)
                self.assertEqual(edges, expected_edges)
                self.assertEqual(edges, sorted(set(edges)))
                self.assertEqual(len(edges), expected_count)
                degrees = [sum(vertex in edge for edge in edges) for vertex in range(1, 10)]
                self.assertEqual(sum(degrees), 2 * expected_count)
                self.assertNotIn(0, degrees)
        self.assertEqual(FIGURES.sample_edges(4, 0, 1), [])
        self.assertEqual(FIGURES.sample_edges(4, 1, 1), list(itertools.combinations(range(1, 5), 2)))

    def test_probability_mass_functions_normalize_and_handle_endpoints(self):
        for trials, p in ((0, 0), (0, 1), (8, 0), (8, 1), (8, 1 / 3), (99, 3 / 99)):
            with self.subTest(trials=trials, p=p):
                masses = [FIGURES.binomial_pmf(trials, p, k) for k in range(trials + 1)]
                self.assertAlmostEqual(sum(masses), 1)
                self.assertTrue(all(0 <= mass <= 1 for mass in masses))
                self.assertEqual(FIGURES.binomial_pmf(trials, p, -1), 0)
                self.assertEqual(FIGURES.binomial_pmf(trials, p, trials + 1), 0)
        self.assertEqual(FIGURES.binomial_pmf(8, 0, 0), 1)
        self.assertEqual(FIGURES.binomial_pmf(8, 1, 8), 1)
        self.assertEqual(FIGURES.poisson_pmf(0, 0), 1)
        self.assertEqual(FIGURES.poisson_pmf(0, 1), 0)
        self.assertEqual(FIGURES.poisson_pmf(3, -1), 0)
        self.assertAlmostEqual(sum(FIGURES.poisson_pmf(3, k) for k in range(100)), 1)

    def test_binomial_with_fixed_mean_moves_toward_poisson(self):
        distances = []
        for n in (25, 100):
            masses = [FIGURES.binomial_pmf(n - 1, 3 / (n - 1), k) for k in range(100)]
            target = [FIGURES.poisson_pmf(3, k) for k in range(100)]
            distances.append(sum(abs(a - b) for a, b in zip(masses, target)) / 2)
            self.assertAlmostEqual(sum(k * mass for k, mass in enumerate(masses)), 3)
        self.assertLess(distances[1], distances[0])
        self.assertLess(distances[1], 0.02)

    def test_exact_mean_one_probability(self):
        for n in (2, 9, 25, 100):
            p = 1 - n ** (-1 / (n - 1))
            with self.subTest(n=n):
                self.assertAlmostEqual(FIGURES.expected_isolates(n, p), 1)

    def test_representative_threshold_scales_do_not_conflate_expectation_and_probability(self):
        small_n, large_n = 1000, 1000000
        for c in (0.5, 1, 1.5):
            means, relative_variances = [], []
            for n in (small_n, large_n):
                p = c * math.log(n) / n
                mean = FIGURES.expected_isolates(n, p)
                means.append(mean)
                relative_variances.append(FIGURES.isolated_variance(n, p) / mean ** 2)
            with self.subTest(c=c):
                if c < 1:
                    self.assertGreater(means[1], means[0])
                    self.assertLess(relative_variances[1], relative_variances[0])
                    self.assertLess(relative_variances[1], 0.002)
                elif c > 1:
                    self.assertLess(means[1], means[0])
                    self.assertLess(means[1], 0.002)
                else:
                    self.assertLess(abs(means[1] - 1), abs(means[0] - 1))
                    self.assertAlmostEqual(means[1], 1, places=3)


class RandomNetworkFigureTests(unittest.TestCase):
    def test_svg_edges_degrees_and_plot_points_match_the_stated_data(self):
        with tempfile.TemporaryDirectory(prefix="random-network-data-test-") as temporary:
            destination = Path(temporary)
            subprocess.run(
                [sys.executable, str(SCRIPT), "--output-dir", str(destination)],
                check=True, capture_output=True, text=True,
            )
            for number, seed in ((1, 20261020), (2, 20261021)):
                with self.subTest(sample=number):
                    root = ET.parse(destination / f"random-network-sample-{number}.svg").getroot()
                    generator = random.Random(seed)
                    expected = [
                        edge for edge in itertools.combinations(range(1, 10), 2)
                        if generator.random() < 1 / 3
                    ]
                    edges = root.findall('.//svg:line[@class="graph-edge"]', SVG_NS)
                    actual = [(int(line.get("data-source")), int(line.get("data-target"))) for line in edges]
                    self.assertEqual(actual, expected)
                    nodes = {
                        int(circle.get("data-node")): circle
                        for circle in root.findall('.//svg:circle[@data-node]', SVG_NS)
                    }
                    self.assertEqual(set(nodes), set(range(1, 10)))
                    for node, circle in nodes.items():
                        self.assertEqual(int(circle.get("data-degree")), sum(node in edge for edge in expected))
                    for line, (u, v) in zip(edges, expected):
                        self.assertEqual(line.get("x1"), nodes[u].get("cx"))
                        self.assertEqual(line.get("y1"), nodes[u].get("cy"))
                        self.assertEqual(line.get("x2"), nodes[v].get("cx"))
                        self.assertEqual(line.get("y2"), nodes[v].get("cy"))

            # Match rendered data coordinates to independently evaluated PMFs.
            root = ET.parse(destination / "random-network-degree-poisson.svg").getroot()
            curves = root.findall(".//svg:polyline", SVG_NS)
            self.assertEqual(len(curves), 3)
            probabilities = [
                [math.comb(trials, k) * (3 / trials) ** k * (1 - 3 / trials) ** (trials - k)
                 for k in range(13)]
                for trials in (24, 99)
            ]
            probabilities.append([math.exp(-3) * 3 ** k / math.factorial(k) for k in range(13)])
            for curve, masses in zip(curves, probabilities):
                points = [tuple(map(float, point.split(","))) for point in curve.get("points").split()]
                self.assertEqual(len(points), 13)
                for k, ((x, y), probability) in enumerate(zip(points, masses)):
                    self.assertAlmostEqual(x, 85 + 525 * k / 12, delta=0.0051)
                    self.assertAlmostEqual(y, 447 - 269 * probability / 0.25, delta=0.0051)

            # The vertical scale is logarithmic, and it shows a count, not a probability.
            root = ET.parse(destination / "random-network-isolated-expectation.svg").getroot()
            curves = root.findall(".//svg:polyline", SVG_NS)
            self.assertEqual(len(curves), 3)
            for n, curve in zip((60, 600, 6000), curves):
                points = [tuple(map(float, point.split(","))) for point in curve.get("points").split()]
                self.assertEqual(len(points), 201)
                for index, (x, y) in enumerate(points):
                    c = 0.5 + index / 200
                    log_expectation = math.log(n) + (n - 1) * math.log1p(-c * math.log(n) / n)
                    expected_y = 438 - 306 * (
                        log_expectation / math.log(10) - math.log10(0.005)
                    ) / (math.log10(200) - math.log10(0.005))
                    self.assertAlmostEqual(x, 85 + 525 * (c - 0.5), delta=0.0051)
                    self.assertAlmostEqual(y, expected_y, delta=0.0051)

    def test_cli_outputs_are_reproducible_accessible_self_contained_svgs(self):
        with tempfile.TemporaryDirectory(prefix="random-network-figures-test-") as temporary:
            destinations = [Path(temporary) / "first", Path(temporary) / "second"]
            for destination in destinations:
                subprocess.run(
                    [sys.executable, str(SCRIPT), "--output-dir", str(destination)],
                    check=True, capture_output=True, text=True,
                )
                self.assertEqual({path.name for path in destination.glob("*.svg")}, SVG_NAMES)
            for name in sorted(SVG_NAMES):
                with self.subTest(name=name):
                    contents = (destinations[0] / name).read_bytes()
                    self.assertEqual(contents, (destinations[1] / name).read_bytes())
                    root = ET.fromstring(contents)
                    self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                    self.assertTrue(root.get("viewBox"))
                    self.assertTrue(root.findtext("svg:title", namespaces=SVG_NS))
                    self.assertTrue(root.findtext("svg:desc", namespaces=SVG_NS))
                    visible_labels = [
                        "".join(element.itertext()).strip()
                        for element in root.findall(".//svg:text", SVG_NS)
                    ]
                    self.assertGreaterEqual(len([label for label in visible_labels if label]), 2)
                    self.assertNotRegex(contents.decode().lower(), r"author[ -]created")
                    self.assertFalse(root.findall(".//svg:image", SVG_NS))
                    for element in root.iter():
                        for key, value in element.attrib.items():
                            if key.rsplit("}", 1)[-1] == "href":
                                self.assertTrue(value.startswith("#"), value)
                    if "degree-poisson" in name:
                        text = " ".join(visible_labels).lower()
                        self.assertIn("binomial", text)
                        self.assertIn("poisson", text)
                    elif "isolated-expectation" in name:
                        text = " ".join(visible_labels).lower()
                        self.assertRegex(text, r"expect(?:ed|ation)")


if __name__ == "__main__":
    unittest.main()
