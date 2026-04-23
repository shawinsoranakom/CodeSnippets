def compare_routed_experts(
    baseline: list[np.ndarray],
    reference: list[np.ndarray],
    threshold: float = 0.05,
) -> float:
    """Compare two runs of routed experts. Returns mismatch ratio.

    Raises AssertionError if ratio exceeds threshold.
    """
    assert len(baseline) == len(reference), (
        f"Length mismatch: {len(baseline)} vs {len(reference)}"
    )

    total_elements = 0
    total_mismatches = 0

    for i, (base, ref) in enumerate(zip(baseline, reference)):
        min_len = min(len(base), len(ref))
        max_len = max(len(base), len(ref))
        if min_len == 0:
            continue

        base_trimmed = base[:min_len]
        ref_trimmed = ref[:min_len]

        matches = 0
        for a, b in zip(base_trimmed, ref_trimmed):
            if a.sum() != b.sum():
                break
            matches += 1

        total_mismatches += max_len - matches
        total_elements += max_len

        if matches < min_len or len(base) != len(ref):
            print(
                f"  Prompt {i}: routed_experts len={len(base)} vs {len(ref)}, "
                f"mismatches={max_len - matches}/{max_len}"
            )

    if total_elements == 0:
        raise ValueError("No elements to compare")

    mismatch_ratio = total_mismatches / total_elements
    print(
        f"Routed experts mismatches: {total_mismatches}/{total_elements} "
        f"({mismatch_ratio:.4%})"
    )

    assert mismatch_ratio < threshold, (
        f"Too many mismatches: {total_mismatches}/{total_elements} "
        f"({mismatch_ratio:.4%}) exceeds threshold {threshold:.4%}"
    )

    return mismatch_ratio