def main():
    parser = argparse.ArgumentParser(
        description="Benchmark pickle unpickling performance for large objects"
    )
    parser.add_argument(
        '--sizes',
        type=int,
        nargs='+',
        default=None,
        metavar='MiB',
        help=f'Object sizes to test in MiB (default: {DEFAULT_SIZES_MIB})'
    )
    parser.add_argument(
        '--protocol',
        type=int,
        default=5,
        choices=[0, 1, 2, 3, 4, 5],
        help='Pickle protocol version (default: 5)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=3,
        help='Number of benchmark iterations (default: 3)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'markdown', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        metavar='PYTHON',
        help='Path to baseline Python interpreter for comparison (e.g., ../main-build/python)'
    )
    parser.add_argument(
        '--antagonistic',
        action='store_true',
        help='Run antagonistic/malicious pickle tests (DoS protection benchmark)'
    )

    args = parser.parse_args()

    # Handle antagonistic mode
    if args.antagonistic:
        # Antagonistic mode uses claimed sizes in MB, not actual data sizes
        if args.sizes is None:
            claimed_sizes_mb = AntagonisticTestSuite.DEFAULT_ANTAGONISTIC_SIZES_MB
        else:
            claimed_sizes_mb = args.sizes

        print(f"Running ANTAGONISTIC pickle benchmark (DoS protection test)...")
        print(f"Claimed sizes: {claimed_sizes_mb} MiB (actual data: 1KB each)")
        print(f"NOTE: These pickles will FAIL to unpickle (expected)")
        print()

        # Run antagonistic benchmark suite
        suite = AntagonisticTestSuite(claimed_sizes_mb)
        results = suite.run_all_tests()

        # Format and display results
        if args.baseline:
            # Verify baseline Python exists
            baseline_path = Path(args.baseline)
            if not baseline_path.exists():
                print(f"Error: Baseline Python not found: {args.baseline}", file=sys.stderr)
                return 1

            # Run baseline benchmark
            baseline_results = Comparator.run_baseline_benchmark(args.baseline, args)

            # Show comparison
            comparison_output = Comparator.format_antagonistic_comparison(results, baseline_results)
            print(comparison_output)
        else:
            # Format and display results
            output = _format_output(results, args.format, is_antagonistic=True)
            print(output)

    else:
        # Normal mode: legitimate pickle benchmarks
        # Convert sizes from MiB to bytes
        if args.sizes is None:
            sizes_bytes = DEFAULT_SIZES
        else:
            sizes_bytes = [size * (1 << 20) for size in args.sizes]

        print(f"Running pickle benchmark with protocol {args.protocol}...")
        print(f"Test sizes: {[f'{s/(1<<20):.2f}MiB' for s in sizes_bytes]}")
        print(f"Iterations per test: {args.iterations}")
        print()

        # Run benchmark suite
        suite = TestSuite(sizes_bytes, args.protocol, args.iterations)
        results = suite.run_all_tests()

        # If baseline comparison requested, run baseline and compare
        if args.baseline:
            # Verify baseline Python exists
            baseline_path = Path(args.baseline)
            if not baseline_path.exists():
                print(f"Error: Baseline Python not found: {args.baseline}", file=sys.stderr)
                return 1

            # Run baseline benchmark
            baseline_results = Comparator.run_baseline_benchmark(args.baseline, args)

            # Show comparison
            comparison_output = Comparator.format_comparison(results, baseline_results)
            print(comparison_output)

        else:
            # Format and display results
            output = _format_output(results, args.format, is_antagonistic=False)
            print(output)

    return 0