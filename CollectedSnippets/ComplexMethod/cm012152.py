def _build_mismatch_report(
    all_fingerprints: list[tuple[object, ...]],
    rank: int,
    world_size: int,
) -> str:
    """Build diagnostic report for SPMD graph mismatch."""
    lines = [
        "=" * 80,
        f"SPMD GRAPH MISMATCH — rank {rank}, world_size={world_size}",
        "=" * 80,
    ]

    # Node count per rank
    counts = [len(t) for t in all_fingerprints]
    lines.append("NODE COUNTS PER RANK:")
    for r in range(world_size):
        marker = " <--" if counts[r] != counts[0] else ""
        lines.append(f"  rank {r}: {counts[r]} call_function nodes{marker}")
    lines.append("")

    # Find entries that differ
    ref = all_fingerprints[0]
    for r in range(1, world_size):
        other = all_fingerprints[r]
        if other == ref:
            continue
        lines.append(f"DIFFS rank 0 vs rank {r}:")

        # Show first few positional differences
        max_diffs = 10
        shown = 0
        for i, (a, b) in enumerate(zip(ref, other)):
            if a != b and shown < max_diffs:
                lines.append(f"  node {i}:")
                lines.append(f"    rank 0: {_entry_target(a)}{_entry_metadata(a)}")
                lines.append(f"    rank {r}: {_entry_target(b)}{_entry_metadata(b)}")
                shown += 1

        # Also show count-based diffs for op targets
        ref_targets = [_entry_target(e) for e in ref]
        other_targets = [_entry_target(e) for e in other]

        ref_counts = Counter(ref_targets)
        other_counts = Counter(other_targets)
        only_ref = ref_counts - other_counts
        only_other = other_counts - ref_counts
        if only_ref:
            lines.append("  Only on rank 0:")
            for op, cnt in only_ref.most_common(10):
                lines.append(f"    {op} (x{cnt})")
        if only_other:
            lines.append(f"  Only on rank {r}:")
            for op, cnt in only_other.most_common(10):
                lines.append(f"    {op} (x{cnt})")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)