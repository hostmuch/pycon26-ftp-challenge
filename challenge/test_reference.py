# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from __future__ import annotations

import unittest

from graph import BuildGraph, Target
from reference import build_all, topological_sort


def _make_single_graph() -> BuildGraph:
    a = Target(name="a", deps=[], work=10, seed=1)
    return BuildGraph(seed=1, targets={"a": a})


def _make_linear_graph() -> BuildGraph:
    a = Target(name="a", deps=[], work=10, seed=1)
    b = Target(name="b", deps=[a], work=10, seed=1)
    c = Target(name="c", deps=[b], work=10, seed=1)
    return BuildGraph(seed=1, targets={"a": a, "b": b, "c": c})


def _make_diamond_graph() -> BuildGraph:
    a = Target(name="a", deps=[], work=10, seed=1)
    b = Target(name="b", deps=[a], work=10, seed=1)
    c = Target(name="c", deps=[a], work=10, seed=1)
    d = Target(name="d", deps=[b, c], work=10, seed=1)
    return BuildGraph(seed=1, targets={"a": a, "b": b, "c": c, "d": d})


def _make_independent_graph() -> BuildGraph:
    a = Target(name="a", deps=[], work=10, seed=1)
    b = Target(name="b", deps=[], work=10, seed=2)
    c = Target(name="c", deps=[], work=10, seed=3)
    return BuildGraph(seed=1, targets={"a": a, "b": b, "c": c})


def _assert_valid_topological_order(
    test: unittest.TestCase,
    graph: BuildGraph,
    order: list[Target],
) -> None:
    """Assert that order contains all targets and respects dependencies."""
    test.assertEqual(len(order), len(graph))
    seen = set()
    for target in order:
        for dep in target.deps:
            test.assertIn(
                dep.name,
                seen,
                f"{target.name!r} appeared before its dependency {dep.name!r}",
            )
        seen.add(target.name)


class TopologicalSortTest(unittest.TestCase):
    def test_single_target(self) -> None:
        graph = _make_single_graph()
        order = topological_sort(graph)
        self.assertEqual(len(order), 1)
        self.assertEqual(order[0].name, "a")

    def test_linear_chain(self) -> None:
        graph = _make_linear_graph()
        order = topological_sort(graph)
        _assert_valid_topological_order(self, graph, order)
        names = [t.name for t in order]
        self.assertEqual(names, ["a", "b", "c"])

    def test_diamond_graph(self) -> None:
        graph = _make_diamond_graph()
        order = topological_sort(graph)
        _assert_valid_topological_order(self, graph, order)

    def test_independent_targets(self) -> None:
        graph = _make_independent_graph()
        order = topological_sort(graph)
        _assert_valid_topological_order(self, graph, order)

    def test_all_targets_included(self) -> None:
        graph = _make_diamond_graph()
        order = topological_sort(graph)
        order_names = {t.name for t in order}
        self.assertEqual(order_names, set(graph.targets.keys()))


class BuildAllTest(unittest.TestCase):
    def test_single_target(self) -> None:
        graph = _make_single_graph()
        results = build_all(graph)
        self.assertIn("a", results)
        self.assertIsInstance(results["a"], bytes)
        self.assertEqual(len(results["a"]), 32)

    def test_linear_chain(self) -> None:
        graph = _make_linear_graph()
        results = build_all(graph)
        self.assertEqual(len(results), 3)
        # Verify results match manual computation
        expected_a = graph.targets["a"].build({})
        expected_b = graph.targets["b"].build({"a": expected_a})
        expected_c = graph.targets["c"].build({"b": expected_b})
        self.assertEqual(results["a"], expected_a)
        self.assertEqual(results["b"], expected_b)
        self.assertEqual(results["c"], expected_c)

    def test_diamond_graph(self) -> None:
        graph = _make_diamond_graph()
        results = build_all(graph)
        self.assertEqual(len(results), 4)
        expected_a = graph.targets["a"].build({})
        expected_b = graph.targets["b"].build({"a": expected_a})
        expected_c = graph.targets["c"].build({"a": expected_a})
        expected_d = graph.targets["d"].build({"b": expected_b, "c": expected_c})
        self.assertEqual(results["a"], expected_a)
        self.assertEqual(results["b"], expected_b)
        self.assertEqual(results["c"], expected_c)
        self.assertEqual(results["d"], expected_d)

    def test_deterministic(self) -> None:
        graph = _make_diamond_graph()
        results1 = build_all(graph)
        results2 = build_all(graph)
        self.assertEqual(results1, results2)

    def test_all_targets_have_results(self) -> None:
        graph = _make_diamond_graph()
        results = build_all(graph)
        self.assertEqual(set(results.keys()), set(graph.targets.keys()))
