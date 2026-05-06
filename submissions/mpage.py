import threading
from concurrent.futures import ThreadPoolExecutor

from graph import BuildGraph


def build_all(graph: BuildGraph) -> dict[str, bytes]:
    results: dict[str, bytes] = {}
    results_lock = threading.Lock()

    dependents: dict[str, list[str]] = {name: [] for name in graph.targets}
    for name, target in graph.targets.items():
        for dep in target.deps:
            dependents[dep.name].append(name)

    remaining_deps: dict[str, int] = {
        name: len(t.deps) for name, t in graph.targets.items()
    }
    remaining_lock = threading.Lock()

    done_event = threading.Event()
    targets_remaining = len(graph.targets)
    targets_remaining_lock = threading.Lock()

    def build_target(name: str) -> None:
        nonlocal targets_remaining

        target = graph.targets[name]
        with results_lock:
            dep_results = {d.name: results[d.name] for d in target.deps}

        # Build the target twice
        target.build(dep_results)
        result = target.build(dep_results)

        with results_lock:
            results[name] = result

        ready: list[str] = []
        with remaining_lock:
            for dep_name in dependents[name]:
                remaining_deps[dep_name] -= 1
                if remaining_deps[dep_name] == 0:
                    ready.append(dep_name)

        for dep_name in ready:
            executor.submit(build_target, dep_name)

        with targets_remaining_lock:
            targets_remaining -= 1
            if targets_remaining == 0:
                done_event.set()

    initial_ready = [name for name, count in remaining_deps.items() if count == 0]

    executor = ThreadPoolExecutor()
    try:
        for name in initial_ready:
            executor.submit(build_target, name)
        done_event.wait()
    finally:
        executor.shutdown(wait=True)

    return results
