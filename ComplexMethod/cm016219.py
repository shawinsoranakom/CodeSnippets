def _print_operation_distribution(results: list[FuzzerResult]) -> None:
    """Helper function to print operation distribution statistics."""
    total_operation_stats = defaultdict(int)
    total_operations = 0

    # Collect operation stats from all successful results
    for result in results:
        if result.success and result.operation_stats:
            for op_name, count in result.operation_stats.items():
                total_operation_stats[op_name] += count
                total_operations += count

    if total_operation_stats:
        persist_print("\n📊 OPERATION DISTRIBUTION")
        persist_print("=" * 60)
        persist_print(f"Total operations executed: {total_operations}")
        persist_print("")

        # Sort operations by count (descending) for better readability
        sorted_ops = sorted(
            total_operation_stats.items(), key=lambda x: x[1], reverse=True
        )

        for op_name, count in sorted_ops:
            percentage = (count / total_operations * 100) if total_operations > 0 else 0
            persist_print(f"  {op_name:<30} {count:>6} times ({percentage:>5.1f}%)")
    else:
        persist_print(
            "\n📊 No operation statistics collected (no successful runs with stats)"
        )