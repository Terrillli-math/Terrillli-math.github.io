"""Independent finite-graph checks for the ERGM study note and figures."""

from collections import Counter
from fractions import Fraction
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_ergm_figures", PROJECT / "scripts/generate_ergm_figures.py")
ERGM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ERGM)


class FiniteGraphTests(unittest.TestCase):
    def test_four_node_example(self):
        stats = ERGM.graph_statistics(4, ERGM.EXAMPLE_EDGES)
        self.assertEqual(stats, {"edges": 4, "degrees": (2, 2, 3, 1), "triangles": 1})
        self.assertEqual(sum(stats["degrees"]), 2 * stats["edges"])
        self.assertEqual(sum(x * d for x, d in zip(ERGM.EXAMPLE_SCORES, stats["degrees"])), 7)

    def test_all_four_node_graph_classes(self):
        # Counts can be checked from graph shapes: m=3 has four triangles,
        # four stars, and twelve paths; m=4 has three cycles and twelve paws.
        expected = {
            (0, 0): 1, (1, 0): 6, (2, 0): 15, (3, 0): 16, (3, 1): 4,
            (4, 0): 3, (4, 1): 12, (5, 2): 6, (6, 4): 1,
        }
        actual = Counter()
        for edges in ERGM.graph_space(4):
            stats = ERGM.graph_statistics(4, edges)
            actual[stats["edges"], stats["triangles"]] += 1
        self.assertEqual(actual, expected)
        self.assertEqual(sum(actual.values()), 64)

    def test_exact_triangle_distribution(self):
        # Each four-node graph with m edges has numerator 2**m over 3**6.
        expected = {0: Fraction(249, 729), 1: Fraction(224, 729),
                    2: Fraction(192, 729), 3: Fraction(0), 4: Fraction(64, 729)}
        probabilities = ERGM.triangle_distribution(4, Fraction(2, 3))
        self.assertEqual(probabilities, expected)
        self.assertEqual(sum(probabilities.values()), 1)
        self.assertEqual(sum(t * p for t, p in probabilities.items()), Fraction(32, 27))
        self.assertEqual(ERGM.triangle_distribution(4, Fraction(0))[0], 1)
        self.assertEqual(ERGM.triangle_distribution(4, Fraction(1))[4], 1)

    def test_eight_graph_ergm(self):
        kappa, distribution = ERGM.edge_triangle_distribution(3, -math.log(2), math.log(4))
        self.assertAlmostEqual(kappa, 15 / 4)
        self.assertAlmostEqual(sum(p for _, p in distribution), 1)
        expected = {0: Fraction(4, 15), 1: Fraction(2, 15),
                    2: Fraction(1, 15), 3: Fraction(2, 15)}
        for edges, probability in distribution:
            self.assertAlmostEqual(probability, float(expected[len(edges)]))
        self.assertAlmostEqual(sum(len(edges) * p for edges, p in distribution), 6 / 5)
        self.assertAlmostEqual(sum(p for edges, p in distribution if (1, 3) in edges), 2 / 5)
        for rest, conditional in [((), 1 / 3), (((1, 2), (2, 3)), 2 / 3)]:
            masses = dict(distribution)
            minus = masses[rest]
            plus = masses[tuple(sorted((*rest, (1, 3))))]
            self.assertAlmostEqual(plus / (minus + plus), conditional)

    def test_fixed_score_model_normalizes_and_has_correct_score(self):
        n, x = 4, ERGM.EXAMPLE_SCORES
        b0, b1 = -math.log(3), math.log(2)
        logmass = lambda edges, a, b: ERGM.logistic_log_likelihood(n, edges, x, a, b)
        self.assertAlmostEqual(sum(math.exp(logmass(edges, b0, b1)) for edges in ERGM.graph_space(n)), 1)
        pair_probabilities = {(1, 2): Fraction(2, 5), (1, 3): Fraction(2, 5),
                              (1, 4): Fraction(4, 7), (2, 3): Fraction(4, 7),
                              (2, 4): Fraction(8, 11), (3, 4): Fraction(8, 11)}
        probabilities = []
        score1 = 0
        for (i, j), probability in pair_probabilities.items():
            self.assertAlmostEqual(ERGM.logistic(b0 + b1 * (x[i - 1] + x[j - 1])), float(probability))
            present = (i, j) in ERGM.EXAMPLE_EDGES
            probabilities.append(float(probability if present else 1 - probability))
            score1 += (int(present) - float(probability)) * (x[i - 1] + x[j - 1])
        expected_mass = math.prod(probabilities)
        self.assertAlmostEqual(math.exp(logmass(ERGM.EXAMPLE_EDGES, b0, b1)), expected_mass)
        h = 1e-6
        observed_score = (logmass(ERGM.EXAMPLE_EDGES, b0, b1 + h) - logmass(ERGM.EXAMPLE_EDGES, b0, b1 - h)) / (2 * h)
        self.assertAlmostEqual(observed_score, score1, places=8)
        self.assertGreater(ERGM.logistic(1000), 0.999999999)
        self.assertLess(ERGM.logistic(-1000), 0.000000001)

    def test_edge_only_mle_and_edge_triangle_score(self):
        # The edge-only likelihood is largest at p=4/6 for the example.
        likelihood = lambda p: p ** 4 * (1 - p) ** 2
        optimum = likelihood(2 / 3)
        self.assertTrue(all(likelihood(p) < optimum for p in (0.4, 0.6, 0.7, 0.9)))
        a, b, h = -0.7, 0.4, 1e-6
        normalizer, distribution = ERGM.edge_triangle_distribution(4, a, b)
        means = [sum(ERGM.graph_statistics(4, e)[key] * p for e, p in distribution) for key in ("edges", "triangles")]
        derivative = lambda da, db: math.log(ERGM.edge_triangle_distribution(4, a + da, b + db)[0])
        self.assertAlmostEqual((derivative(h, 0) - derivative(-h, 0)) / (2 * h), means[0], places=8)
        self.assertAlmostEqual((derivative(0, h) - derivative(0, -h)) / (2 * h), means[1], places=8)

    def test_figure_data_and_determinism(self):
        with tempfile.TemporaryDirectory(prefix="ergm-svg-") as temporary:
            output = Path(temporary)
            ERGM.generate(output)
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            ERGM.generate(output)
            self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
            self.assertEqual(len(before), 3)
            for content in before.values():
                svg = ET.fromstring(content)
                self.assertEqual(svg.get("role"), "img")
                text = " ".join(svg.itertext()).lower()
                self.assertNotIn("author-created", text)
                self.assertNotIn("seed", text)
            ns = {"s": "http://www.w3.org/2000/svg"}
            graph = ET.fromstring(before["ergm-four-nodes.svg"])
            edges = {(int(e.get("data-source")), int(e.get("data-target"))) for e in graph.findall('.//s:line[@class="graph-edge"]', ns)}
            self.assertEqual(edges, set(ERGM.EXAMPLE_EDGES))
            toggle = ET.fromstring(before["ergm-edge-toggle.svg"])
            self.assertEqual([e.get("data-probability") for e in toggle.findall('.//s:line[@class="candidate-edge"]', ns)], ["1/3", "2/3"])
            check = ET.fromstring(before["ergm-triangle-check.svg"])
            bars = {int(e.get("data-triangles")): Fraction(e.get("data-probability")) for e in check.findall('.//s:rect[@class="probability-bar"]', ns)}
            self.assertEqual(bars, ERGM.triangle_distribution(4, Fraction(2, 3)))


if __name__ == "__main__":
    unittest.main()
