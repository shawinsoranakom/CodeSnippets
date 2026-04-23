def compiled_module_main(
    benchmark_name: str, benchmark_compiled_module_fn: BenchmarkCallableType
) -> None:
    """
    This is the function called in __main__ block of a compiled module.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark-kernels",
        "-k",
        action="store_true",
        help="Whether to benchmark each individual kernels",
    )
    parser.add_argument(
        "--benchmark-all-configs",
        "-c",
        action="store_true",
        help="Whether to benchmark each individual config for a kernel",
    )
    parser.add_argument(
        "--profile",
        "-p",
        action="store_true",
        help="Whether to profile the compiled module",
    )
    parser.add_argument(
        "--cuda-memory-snapshot",
        action="store_true",
        help="""
            Whether to collect CUDA memory snapshot. Refer to
            "https://pytorch.org/blog/understanding-gpu-memory-1/
            for details about how to visualize the collected snapshot
        """,
    )
    parser.add_argument(
        "--ncu",
        action="store_true",
        help="Whether to run ncu analysis",
    )
    parser.add_argument(
        "--ncu-kernel-regex",
        type=str,
        default=None,
        help=(
            "Filter kernels profiled by NCU using a regex (e.g., '^triton_.*'). "
            "Maps to '--kernel-name regex:<regex>'. "
            "If None, NCU will profile all kernels."
        ),
    )
    parser.add_argument(
        "--ncu-metrics",
        type=str,
        default=None,
        help=(
            "Comma-separated list of NCU metrics to collect (e.g., 'dram__bytes.sum.per_second'). "
            "If None, NCU will use '--set full'."
        ),
    )
    parser.add_argument(
        "--times",
        type=int,
        default=10,
        help="Number of times to run each benchmark iteration",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=10,
        help="Number of repetitions of each benchmark run",
    )

    args = parser.parse_args()

    if args.benchmark_kernels:
        benchmark_all_kernels(benchmark_name, args.benchmark_all_configs)
    else:
        times = args.times
        repeat = args.repeat

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        wall_time_ms = benchmark_compiled_module_fn(times=times, repeat=repeat) * 1000

        if torch.cuda.is_available():
            peak_mem = torch.cuda.max_memory_allocated()
            print(f"Peak GPU memory usage {peak_mem / 1e6:.3f} MB")

        if torch.cuda.is_available() and args.cuda_memory_snapshot:
            collect_memory_snapshot(benchmark_compiled_module_fn)

        if args.profile:
            perf_profile(
                wall_time_ms,
                times,
                repeat,
                benchmark_name,
                benchmark_compiled_module_fn,
            )
        if args.ncu:
            ncu_analyzer(
                benchmark_name,
                benchmark_compiled_module_fn,
                args=args,
            )