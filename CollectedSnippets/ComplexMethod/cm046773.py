def _compute_num_dense_layers(text_config, total_layers: int) -> int:
    """Count how many layers use dense MLP instead of MoE."""
    first_k = getattr(text_config, "first_k_dense_replace", None)
    if first_k is not None:
        return min(int(first_k), total_layers)

    sparse_step = getattr(text_config, "decoder_sparse_step", None)
    mlp_only = getattr(text_config, "mlp_only_layers", None) or []
    if sparse_step is not None and sparse_step > 0:
        mlp_only_set = set(mlp_only)
        moe_count = sum(
            1
            for i in range(total_layers)
            if i not in mlp_only_set and (i + 1) % sparse_step == 0
        )
        return total_layers - moe_count

    return 0