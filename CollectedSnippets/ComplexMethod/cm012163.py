def _sfdp_params_check(match):
    assert all(k in match.kwargs for k in ("query", "key", "value"))
    query = match.kwargs["query"].meta["val"]
    key = match.kwargs["key"].meta["val"]
    value = match.kwargs["value"].meta["val"]
    if not (query.dtype == key.dtype == value.dtype) or not (
        query.device == key.device == value.device
    ):
        return False
    # fused kernels use tf32
    if (
        query.device.type == "cuda"
        and query.dtype == torch.float32
        and torch.backends.cuda.matmul.fp32_precision != "tf32"
    ):
        _warn_tf32_disabled()
        return False

    add_mask_node = filter_nodes(match.nodes, aten.add.Tensor)
    # Has attn_mask add.
    if len(add_mask_node) > 0:
        attn_mask_node = add_mask_node[0].args[1]
        # attn_mask_node may be a float/int number.
        if not hasattr(attn_mask_node, "meta"):
            return False
        attn_mask = attn_mask_node.meta["val"]  # type: ignore[union-attr]
        # Make sure attn_mask.dtype == query.dtype or attn_mask.dtype == torch.bool
        # attn_mask.dtype == torch.float for models like albert.
        if (
            not isinstance(attn_mask, torch.Tensor)
            or not (
                attn_mask.dtype == query.dtype
                or attn_mask.dtype == torch.bool
                or attn_mask.dtype == torch.float
            )
            or query.device != attn_mask.device
            # When we tensorify floats we end up turning floats
            # into 0d scalar tensors. It doesn't make any sense
            # to have a 0d scalar tensor attention mask so
            # conveniently we can insert this check to get
            # tests that erroneously passing in a float
            # attention mask to fail as expected.
            or attn_mask.dim() == 0
        ):
            return False
    return True