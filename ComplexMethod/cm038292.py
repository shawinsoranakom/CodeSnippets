def _extract_data_from_fused_moe_module(
    m: torch.nn.Module,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, int]:
    """
    Extract weights, weight scales and num_topk from FusedMoE module.
    """
    assert isinstance(m, FusedMoE)
    w13 = m.w13_weight
    w13_s = (
        m.w13_weight_scale_inv
        if hasattr(m, "w13_weight_scale_inv")
        else m.w13_weight_scale
    )
    w2 = m.w2_weight
    w2_s = (
        m.w2_weight_scale_inv
        if hasattr(m, "w2_weight_scale_inv")
        else m.w2_weight_scale
    )
    num_topk = m.top_k

    assert isinstance(w13, torch.Tensor)
    assert isinstance(w13_s, torch.Tensor)
    assert isinstance(w2, torch.Tensor)
    assert isinstance(w2_s, torch.Tensor)
    return w13, w13_s, w2, w2_s, num_topk