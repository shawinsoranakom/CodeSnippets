def format_antagonistic_comparison(
        current_results: Dict[str, Dict[str, Any]],
        baseline_results: Dict[str, Dict[str, Any]]
    ) -> str:
        """Format antagonistic benchmark comparison results."""
        lines = []
        lines.append("=" * 100)
        lines.append("Antagonistic Pickle Benchmark Comparison (Memory DoS Protection)")
        lines.append("=" * 100)
        lines.append("")
        lines.append("Legend: Current vs Baseline | Memory Change (- is better, shows memory saved)")
        lines.append("")
        lines.append("This compares TWO types of DoS protection:")
        lines.append("  1. Truncated data → Baseline allocates full claimed size, Current uses chunked reading")
        lines.append("  2. Sparse memo → Baseline uses huge arrays, Current uses dict-based memo")
        lines.append("")

        # Track statistics
        truncated_memory_changes = []
        sparse_memory_changes = []

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

                curr_peak_mb = curr['peak_memory_mb']
                base_peak_mb = base['peak_memory_mb']
                expected_outcome = curr.get('expected_outcome', 'failure')

                mem_change = Comparator.calculate_change(base_peak_mb, curr_peak_mb)
                mem_saved_mb = base_peak_mb - curr_peak_mb

                lines.append(f"\n  {curr['test_name']}")
                lines.append(f"    Memory: {curr_peak_mb:6.2f}MB vs {base_peak_mb:6.2f}MB | "
                           f"{mem_change:+6.1f}% ({mem_saved_mb:+.2f}MB saved)")

                # Track based on test type
                if expected_outcome == 'success':
                    sparse_memory_changes.append(mem_change)
                    if curr.get('baseline_note'):
                        lines.append(f"    Note: {curr['baseline_note']}")
                else:
                    truncated_memory_changes.append(mem_change)
                    claimed_mb = curr.get('claimed_mb', 'N/A')
                    if claimed_mb != 'N/A':
                        lines.append(f"    Claimed: {claimed_mb:,}MB")

                # Show status
                curr_status = curr.get('error_type', 'Unknown')
                base_status = base.get('error_type', 'Unknown')
                if curr_status != base_status:
                    lines.append(f"    Status: {curr_status} (baseline: {base_status})")
                else:
                    lines.append(f"    Status: {curr_status}")

        lines.append("\n" + "=" * 100)
        lines.append("\nSummary:")
        lines.append("")

        if truncated_memory_changes:
            lines.append("  Truncated Data Protection (chunked reading):")
            lines.append(f"    Mean memory change:   {statistics.mean(truncated_memory_changes):+.1f}%")
            lines.append(f"    Median memory change: {statistics.median(truncated_memory_changes):+.1f}%")
            avg_change = statistics.mean(truncated_memory_changes)
            if avg_change < -50:
                lines.append(f"    Result: ✓ Dramatic memory reduction ({avg_change:.1f}%) - DoS protection working!")
            elif avg_change < 0:
                lines.append(f"    Result: ✓ Memory reduced ({avg_change:.1f}%)")
            else:
                lines.append(f"    Result: ⚠ Memory increased ({avg_change:.1f}%) - unexpected!")
            lines.append("")

        if sparse_memory_changes:
            lines.append("  Sparse Memo Protection (dict-based memo):")
            lines.append(f"    Mean memory change:   {statistics.mean(sparse_memory_changes):+.1f}%")
            lines.append(f"    Median memory change: {statistics.median(sparse_memory_changes):+.1f}%")
            avg_change = statistics.mean(sparse_memory_changes)
            if avg_change < -50:
                lines.append(f"    Result: ✓ Dramatic memory reduction ({avg_change:.1f}%) - Dict optimization working!")
            elif avg_change < 0:
                lines.append(f"    Result: ✓ Memory reduced ({avg_change:.1f}%)")
            else:
                lines.append(f"    Result: ⚠ Memory increased ({avg_change:.1f}%) - unexpected!")

        lines.append("")
        lines.append("=" * 100)
        return "\n".join(lines)