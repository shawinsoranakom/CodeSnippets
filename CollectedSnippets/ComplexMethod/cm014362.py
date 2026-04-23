def main() -> None:
    tasks = [
        ("matmul", "x @ y", "torch.sparse.mm(x, y)"),
        ("matmul", "x @ y + 0", "torch.sparse.mm(x, y) + zero"),
    ]

    serialized_results = []
    repeats = 2
    timers = [
        benchmark_utils.Timer(
            stmt=stmt,
            globals={
                "torch": torch if branch == "master" else FauxTorch(torch, overhead_ns),
                "x": gen_sparse(size=size, density=density, dtype=torch.float32),
                "y": torch.rand(size, dtype=torch.float32),
                "zero": torch.zeros(()),
            },
            label=label,
            sub_label=sub_label,
            description=f"size: {size}",
            env=branch,
            num_threads=num_threads,
        )
        for branch, overhead_ns in [("master", None), ("my_branch", 1), ("severe_regression", 10)]
        for label, sub_label, stmt in tasks
        for density in [0.05, 0.1]
        for size in [(8, 8), (32, 32), (64, 64), (128, 128)]
        for num_threads in [1, 4]
    ]

    for i, timer in enumerate(timers * repeats):
        serialized_results.append(pickle.dumps(
            timer.blocked_autorange(min_run_time=0.05)
        ))
        print(f"\r{i + 1} / {len(timers) * repeats}", end="")
        sys.stdout.flush()
    print()

    comparison = benchmark_utils.Compare([
        pickle.loads(i) for i in serialized_results
    ])

    print("== Unformatted " + "=" * 80 + "\n" + "/" * 95 + "\n")
    comparison.print()

    print("== Formatted " + "=" * 80 + "\n" + "/" * 93 + "\n")
    comparison.trim_significant_figures()
    comparison.colorize()
    comparison.print()