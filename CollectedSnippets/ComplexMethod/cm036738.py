def assert_aiter_routing_valid(
    topk_weights: torch.Tensor,
    topk_ids: torch.Tensor,
    top_k: int,
    num_experts: int,
    renormalize: bool,
    routed_scaling_factor: float = 1.0,
):
    """Validate AITER routing outputs are structurally correct.

    AITER grouped_topk is a fundamentally different implementation from
    the Python baseline (different group selection, scoring internals),
    so numerical comparison is not meaningful. Instead we verify the
    outputs satisfy the routing contract: correct shapes, valid expert
    IDs, non-negative weights, and proper normalization."""
    n_tokens = topk_weights.shape[0]

    # Shape
    assert topk_weights.shape == (n_tokens, top_k), (
        f"weights shape {topk_weights.shape} != ({n_tokens}, {top_k})"
    )
    assert topk_ids.shape == (n_tokens, top_k), (
        f"ids shape {topk_ids.shape} != ({n_tokens}, {top_k})"
    )

    # Expert IDs in valid range
    assert (topk_ids >= 0).all() and (topk_ids < num_experts).all(), (
        f"expert IDs out of range [0, {num_experts}): "
        f"min={topk_ids.min().item()}, max={topk_ids.max().item()}"
    )

    # No duplicate expert IDs per token
    for i in range(n_tokens):
        ids = topk_ids[i]
        assert ids.unique().numel() == top_k, (
            f"token {i}: duplicate expert IDs {ids.tolist()}"
        )

    # Weights are non-negative
    assert (topk_weights >= 0).all(), "negative routing weights"

    # If renormalized, weights should sum to ~scaling_factor per token
    # (renormalization to 1.0 happens before scaling)
    if renormalize:
        expected_sum = routed_scaling_factor
        sums = topk_weights.sum(dim=-1)
        torch.testing.assert_close(
            sums,
            torch.full_like(sums, expected_sum),
            atol=1e-3,
            rtol=1e-3,
        )