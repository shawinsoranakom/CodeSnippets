def compare_token_ids(
    baseline: list[list[int]],
    reference: list[list[int]],
) -> float:
    """Compare token IDs from two runs. Returns mismatch ratio."""
    assert len(baseline) == len(reference), (
        f"Length mismatch: {len(baseline)} vs {len(reference)}"
    )

    total_tokens = 0
    total_mismatches = 0

    for i, (base, ref) in enumerate(zip(baseline, reference)):
        min_len = min(len(base), len(ref))
        max_len = max(len(base), len(ref))
        matches = 0
        for a, b in zip(base[:min_len], ref[:min_len]):
            if a != b:
                break
            matches += 1

        total_mismatches += max_len - matches
        total_tokens += max_len

        if matches < min_len or len(base) != len(ref):
            print(
                f"  Prompt {i}: token_ids len={len(base)} vs {len(ref)}, "
                f"mismatches={max_len - matches}/{max_len}"
            )

    if total_tokens == 0:
        raise ValueError("No tokens to compare")

    mismatch_ratio = total_mismatches / total_tokens
    print(
        f"Token ID mismatches: {total_mismatches}/{total_tokens} ({mismatch_ratio:.4%})"
    )
    return mismatch_ratio