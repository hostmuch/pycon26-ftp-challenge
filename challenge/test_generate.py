# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

from __future__ import annotations

import unittest

from generate import (
    generate_chain,
    generate_diamond,
    generate_realistic,
    generate_tree,
    generate_wide,
)


class GenerateWideTest(unittest.TestCase):
    def test_leaf_and_aggregator_ratio(self) -> None:
        graph = generate_wide(100, seed=1)
        leaves = [t for t in graph.targets.values() if not t.deps]
        aggs = [t for t in graph.targets.values() if t.deps]
        self.assertEqual(len(leaves), 90)
        self.assertEqual(len(aggs), 10)

    def test_aggregators_depend_only_on_leaves(self) -> None:
        graph = generate_wide(100, seed=1)
        leaf_names = {t.name for t in graph.targets.values() if not t.deps}
        for t in graph.targets.values():
            if t.deps:
                for dep in t.deps:
                    self.assertIn(dep.name, leaf_names)

    def test_deterministic(self) -> None:
        g1 = generate_wide(50, seed=7)
        g2 = generate_wide(50, seed=7)
        self.assertEqual(len(g1), len(g2))
        for name in g1.targets:
            self.assertIn(name, g2.targets)
            self.assertEqual(g1.targets[name], g2.targets[name])


class GenerateChainTest(unittest.TestCase):
    def test_linear_dependencies(self) -> None:
        graph = generate_chain(5, seed=1)
        self.assertEqual(len(graph), 5)
        for i in range(5):
            t = graph.targets[f"step_{i}"]
            if i == 0:
                self.assertEqual(len(t.deps), 0)
            else:
                self.assertEqual(len(t.deps), 1)
                self.assertEqual(t.deps[0].name, f"step_{i - 1}")

    def test_deterministic(self) -> None:
        g1 = generate_chain(10, seed=42)
        g2 = generate_chain(10, seed=42)
        for name in g1.targets:
            self.assertEqual(g1.targets[name], g2.targets[name])


class GenerateDiamondTest(unittest.TestCase):
    def test_source_has_no_deps(self) -> None:
        graph = generate_diamond(20, seed=1)
        self.assertIn("source_0", graph.targets)
        self.assertEqual(len(graph.targets["source_0"].deps), 0)

    def test_has_fan_and_merge_targets(self) -> None:
        graph = generate_diamond(20, seed=1)
        fan_targets = [n for n in graph.targets if n.startswith("fan_")]
        merge_targets = [n for n in graph.targets if n.startswith("merge_")]
        self.assertGreater(len(fan_targets), 0)
        self.assertGreater(len(merge_targets), 0)

    def test_deterministic(self) -> None:
        g1 = generate_diamond(20, seed=5)
        g2 = generate_diamond(20, seed=5)
        self.assertEqual(len(g1), len(g2))
        for name in g1.targets:
            self.assertEqual(g1.targets[name], g2.targets[name])


class GenerateTreeTest(unittest.TestCase):
    def test_has_leaves_and_parents(self) -> None:
        graph = generate_tree(16, seed=1)
        leaves = [n for n in graph.targets if n.startswith("leaf_")]
        parents = [n for n in graph.targets if n.startswith("parent_")]
        self.assertEqual(len(leaves), 16)
        self.assertGreater(len(parents), 0)

    def test_leaves_have_no_deps(self) -> None:
        graph = generate_tree(8, seed=1)
        for name, t in graph.targets.items():
            if name.startswith("leaf_"):
                self.assertEqual(len(t.deps), 0)

    def test_parents_have_deps(self) -> None:
        graph = generate_tree(8, seed=1)
        for name, t in graph.targets.items():
            if name.startswith("parent_"):
                self.assertGreater(len(t.deps), 0)

    def test_deterministic(self) -> None:
        g1 = generate_tree(16, seed=3)
        g2 = generate_tree(16, seed=3)
        self.assertEqual(len(g1), len(g2))
        for name in g1.targets:
            self.assertEqual(g1.targets[name], g2.targets[name])


class GenerateRealisticTest(unittest.TestCase):
    def test_later_layers_have_deps(self) -> None:
        graph = generate_realistic(50, seed=1)
        non_first = [
            t
            for name, t in graph.targets.items()
            if not name.startswith("target_L0_") and name.startswith("target_")
        ]
        for t in non_first:
            self.assertGreater(len(t.deps), 0)

    def test_deterministic(self) -> None:
        g1 = generate_realistic(30, seed=10)
        g2 = generate_realistic(30, seed=10)
        self.assertEqual(len(g1), len(g2))
        for name in g1.targets:
            self.assertEqual(g1.targets[name], g2.targets[name])


if __name__ == "__main__":
    unittest.main()
