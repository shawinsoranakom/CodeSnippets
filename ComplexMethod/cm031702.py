def main(opts):
    global WORK_SCALE
    if not hasattr(sys, "_is_gil_enabled") or sys._is_gil_enabled():
        sys.stderr.write("expected to be run with the  GIL disabled\n")

    benchmark_names = opts.benchmarks
    if benchmark_names:
        for name in benchmark_names:
            if name not in ALL_BENCHMARKS:
                sys.stderr.write(f"Unknown benchmark: {name}\n")
                sys.exit(1)
    else:
        benchmark_names = ALL_BENCHMARKS.keys()

    WORK_SCALE = opts.scale

    if not opts.baseline_only:
        initialize_threads(opts)

    do_bench = not opts.baseline_only and not opts.parallel_only
    for name in benchmark_names:
        func = ALL_BENCHMARKS[name]
        if do_bench:
            benchmark(func)
            continue

        if opts.parallel_only:
            delta_ns = bench_parallel(func)
        else:
            delta_ns = bench_one_thread(func)

        time_ms = delta_ns / 1_000_000
        print(f"{func.__name__:<18} {time_ms:.1f} ms")