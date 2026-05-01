# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from __future__ import annotations

import json
import tempfile
import unittest

from graph import BuildGraph, Target


class TargetEqualityTest(unittest.TestCase):
    def test_equal_targets(self) -> None:
        a = Target(name="a", deps=[], work=100, seed=1)
        b = Target(name="a", deps=[], work=100, seed=1)
        self.assertEqual(a, b)

    def test_equal_targets_with_deps(self) -> None:
        dep_a = Target(name="dep", deps=[], work=50, seed=1)
        dep_b = Target(name="dep", deps=[], work=50, seed=1)
        a = Target(name="a", deps=[dep_a], work=100, seed=1)
        b = Target(name="a", deps=[dep_b], work=100, seed=1)
        self.assertEqual(a, b)

    def test_different_name(self) -> None:
        a = Target(name="a", deps=[], work=100, seed=1)
        b = Target(name="b", deps=[], work=100, seed=1)
        self.assertNotEqual(a, b)

    def test_different_work(self) -> None:
        a = Target(name="a", deps=[], work=100, seed=1)
        b = Target(name="a", deps=[], work=200, seed=1)
        self.assertNotEqual(a, b)

    def test_different_seed(self) -> None:
        a = Target(name="a", deps=[], work=100, seed=1)
        b = Target(name="a", deps=[], work=100, seed=2)
        self.assertNotEqual(a, b)

    def test_different_deps(self) -> None:
        dep1 = Target(name="x", deps=[], work=50, seed=1)
        dep2 = Target(name="y", deps=[], work=50, seed=1)
        a = Target(name="a", deps=[dep1], work=100, seed=1)
        b = Target(name="a", deps=[dep2], work=100, seed=1)
        self.assertNotEqual(a, b)

    def test_not_equal_to_non_target(self) -> None:
        a = Target(name="a", deps=[], work=100, seed=1)
        self.assertNotEqual(a, "not a target")


class TargetBuildTest(unittest.TestCase):
    def test_build_is_deterministic(self) -> None:
        t = Target(name="a", deps=[], work=100, seed=42)
        result1 = t.build({})
        result2 = t.build({})
        self.assertEqual(result1, result2)

    def test_build_no_deps(self) -> None:
        t = Target(name="a", deps=[], work=100, seed=42)
        result = t.build({})
        self.assertIsInstance(result, bytes)
        self.assertEqual(len(result), 32)  # SHA-256 digest

    def test_build_with_deps(self) -> None:
        dep = Target(name="dep", deps=[], work=50, seed=1)
        dep_result = dep.build({})

        t = Target(name="a", deps=["dep"], work=100, seed=1)
        result_with_dep = t.build({"dep": dep_result})
        result_without_dep = t.build({})
        self.assertNotEqual(result_with_dep, result_without_dep)

    def test_different_deps_produce_different_results(self) -> None:
        t = Target(name="a", deps=["d"], work=100, seed=1)
        result1 = t.build({"d": b"aaa"})
        result2 = t.build({"d": b"bbb"})
        self.assertNotEqual(result1, result2)

    def test_different_seeds_produce_different_results(self) -> None:
        t1 = Target(name="a", deps=[], work=100, seed=1)
        t2 = Target(name="a", deps=[], work=100, seed=2)
        self.assertNotEqual(t1.build({}), t2.build({}))


class BuildGraphLoadSaveTest(unittest.TestCase):
    def _make_graph(self) -> BuildGraph:
        a = Target(name="a", deps=[], work=100, seed=7)
        b = Target(name="b", deps=[a], work=200, seed=7)
        targets = {"a": a, "b": b}
        return BuildGraph(seed=7, targets=targets)

    def test_round_trip(self) -> None:
        graph = self._make_graph()
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            graph.save(f.name)
            loaded = BuildGraph.load(f.name)

        self.assertEqual(len(loaded), len(graph))
        for name, target in graph.targets.items():
            self.assertIn(name, loaded.targets)
            self.assertEqual(loaded.targets[name], target)

    def test_len(self) -> None:
        graph = self._make_graph()
        self.assertEqual(len(graph), 2)


class BuildGraphValidationTest(unittest.TestCase):
    def _write_graph_json(self, path: str, seed: int, targets: dict) -> None:
        with open(path, "w") as f:
            json.dump({"seed": seed, "targets": targets}, f)

    def test_missing_dep_raises(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w") as f:
            self._write_graph_json(
                f.name, 1, {"a": {"deps": ["nonexistent"], "work": 100}}
            )
            with self.assertRaises(ValueError):
                BuildGraph.load(f.name)

    def test_cycle_raises(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w") as f:
            self._write_graph_json(
                f.name,
                1,
                {
                    "a": {"deps": ["b"], "work": 100},
                    "b": {"deps": ["a"], "work": 100},
                },
            )
            with self.assertRaises(ValueError):
                BuildGraph.load(f.name)

    def test_valid_graph_no_error(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w") as f:
            self._write_graph_json(
                f.name,
                1,
                {
                    "a": {"deps": [], "work": 100},
                    "b": {"deps": ["a"], "work": 100},
                },
            )
            graph = BuildGraph.load(f.name)
            self.assertEqual(len(graph), 2)


if __name__ == "__main__":
    unittest.main()
