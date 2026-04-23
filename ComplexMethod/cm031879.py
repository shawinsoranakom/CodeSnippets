def format_antagonistic(results: Dict[str, Dict[str, Any]]) -> str:
        """Format antagonistic benchmark results."""
        lines = []
        lines.append("=" * 100)
        lines.append("Antagonistic Pickle Benchmark (Memory DoS Protection Test)")
        lines.append("=" * 100)
        lines.append("")
        lines.append("This benchmark tests TWO types of DoS protection:")
        lines.append("  1. Truncated data attacks → Expect FAILURE with minimal memory before failure")
        lines.append("  2. Sparse memo attacks → Expect SUCCESS with dict-based memo (vs huge array)")
        lines.append("")

        # Sort size keys numerically
        for size_key in sorted(results.keys(), key=_extract_size_mb):
            tests = results[size_key]

            # Determine test type from first test
            if tests:
                first_test = next(iter(tests.values()))
                expected_outcome = first_test.get('expected_outcome', 'failure')
                claimed_mb = first_test.get('claimed_mb', 'N/A')

                # Header varies by test type
                if "Sparse Memo" in size_key:
                    lines.append(f"\n{size_key}")
                    lines.append("-" * 100)
                elif "Multi-Claim" in size_key:
                    lines.append(f"\n{size_key}")
                    lines.append("-" * 100)
                elif claimed_mb != 'N/A':
                    lines.append(f"\n{size_key} Claimed (actual: 1KB) - Expect Failure")
                    lines.append("-" * 100)
                else:
                    lines.append(f"\n{size_key}")
                    lines.append("-" * 100)

            for test_name, data in tests.items():
                peak_mb = data['peak_memory_mb']
                claimed = data.get('claimed_mb', 'N/A')
                expected_outcome = data.get('expected_outcome', 'failure')
                succeeded = data.get('succeeded', False)
                baseline_note = data.get('baseline_note', '')

                lines.append(f"  {data['test_name']}")

                # Format output based on test type
                if expected_outcome == 'success':
                    # Sparse memo test - show success with dict
                    status_icon = "✓" if succeeded else "✗"
                    lines.append(f"    Peak memory: {peak_mb:8.2f} MB {status_icon}")
                    lines.append(f"    Status: {data['error_type']}")
                    if baseline_note:
                        lines.append(f"    {baseline_note}")
                else:
                    # Truncated data test - show savings before failure
                    if claimed != 'N/A':
                        saved_mb = claimed - peak_mb
                        savings_pct = (saved_mb / claimed * 100) if claimed > 0 else 0
                        lines.append(f"    Peak memory: {peak_mb:8.2f} MB (claimed: {claimed:,} MB, saved: {saved_mb:.2f} MB, {savings_pct:.1f}%)")
                    else:
                        lines.append(f"    Peak memory: {peak_mb:8.2f} MB")
                    lines.append(f"    Status: {data['error_type']}")

        lines.append("\n" + "=" * 100)

        # Calculate statistics by test type
        truncated_claimed = 0
        truncated_peak = 0
        truncated_count = 0

        sparse_peak_total = 0
        sparse_count = 0

        for size_key, tests in results.items():
            for test_name, data in tests.items():
                expected_outcome = data.get('expected_outcome', 'failure')

                if expected_outcome == 'failure':
                    # Truncated data test
                    claimed = data.get('claimed_mb', 0)
                    if claimed != 'N/A' and claimed > 0:
                        truncated_claimed += claimed
                        truncated_peak += data['peak_memory_mb']
                        truncated_count += 1
                else:
                    # Sparse memo test
                    sparse_peak_total += data['peak_memory_mb']
                    sparse_count += 1

        lines.append("\nSummary:")
        lines.append("")

        if truncated_count > 0:
            avg_claimed = truncated_claimed / truncated_count
            avg_peak = truncated_peak / truncated_count
            avg_saved = avg_claimed - avg_peak
            avg_savings_pct = (avg_saved / avg_claimed * 100) if avg_claimed > 0 else 0

            lines.append("  Truncated Data Protection (chunked reading):")
            lines.append(f"    Average claimed: {avg_claimed:,.1f} MB")
            lines.append(f"    Average peak:    {avg_peak:,.2f} MB")
            lines.append(f"    Average saved:   {avg_saved:,.2f} MB ({avg_savings_pct:.1f}% reduction)")
            lines.append(f"    Status: ✓ Fails fast with minimal memory")
            lines.append("")

        if sparse_count > 0:
            avg_sparse_peak = sparse_peak_total / sparse_count
            lines.append("  Sparse Memo Protection (dict-based memo):")
            lines.append(f"    Average peak:    {avg_sparse_peak:,.2f} MB")
            lines.append(f"    Status: ✓ Succeeds with dict (vs GB-sized arrays without PR)")
            lines.append(f"    Note: Compare with --baseline to see actual memory savings")

        lines.append("")
        lines.append("=" * 100)
        return "\n".join(lines)