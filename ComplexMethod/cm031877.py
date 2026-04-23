def format_comparison(
        current_results: Dict[str, Dict[str, Any]],
        baseline_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """Format comparison results as readable text."""
        lines = []
        lines.append("=" * 100)
        lines.append("Pickle Unpickling Benchmark Comparison")
        lines.append("=" * 100)
        lines.append("")
        lines.append("Legend: Current vs Baseline | % Change (+ is slower/more memory, - is faster/less memory)")
        lines.append("")

        # Sort size keys numerically
        for size_key in sorted(current_results.keys(), key=_extract_size_mb):
            if size_key not in baseline_results:
                continue

            lines.append(f"\n{size_key} Comparison")
            lines.append("-" * 100)

            current_tests = current_results[size_key]
            baseline_tests = baseline_results[size_key]

            for test_name in sorted(current_tests.keys()):
                if test_name not in baseline_tests:
                    continue

                curr = current_tests[test_name]
                base = baseline_tests[test_name]

                time_change = Comparator.calculate_change(
                    base['time']['mean'], curr['time']['mean']
                )
                mem_change = Comparator.calculate_change(
                    base['memory_peak_mb'], curr['memory_peak_mb']
                )

                lines.append(f"\n  {curr['test_name']}")
                lines.append(f"    Time:   {curr['time']['mean']*1000:6.2f}ms vs {base['time']['mean']*1000:6.2f}ms | "
                           f"{time_change:+6.1f}%")
                lines.append(f"    Memory: {curr['memory_peak_mb']:6.2f}MB vs {base['memory_peak_mb']:6.2f}MB | "
                           f"{mem_change:+6.1f}%")

        lines.append("\n" + "=" * 100)
        lines.append("\nSummary:")

        # Calculate overall statistics
        time_changes = []
        mem_changes = []

        for size_key in current_results.keys():
            if size_key not in baseline_results:
                continue
            for test_name in current_results[size_key].keys():
                if test_name not in baseline_results[size_key]:
                    continue
                curr = current_results[size_key][test_name]
                base = baseline_results[size_key][test_name]

                time_changes.append(Comparator.calculate_change(
                    base['time']['mean'], curr['time']['mean']
                ))
                mem_changes.append(Comparator.calculate_change(
                    base['memory_peak_mb'], curr['memory_peak_mb']
                ))

        if time_changes:
            lines.append(f"  Time change:   mean={statistics.mean(time_changes):+.1f}%, "
                       f"median={statistics.median(time_changes):+.1f}%")
        if mem_changes:
            lines.append(f"  Memory change: mean={statistics.mean(mem_changes):+.1f}%, "
                       f"median={statistics.median(mem_changes):+.1f}%")

        lines.append("=" * 100)
        return "\n".join(lines)