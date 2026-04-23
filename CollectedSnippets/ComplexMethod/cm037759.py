def invoke_fused_moe_triton_kernel(
    A: torch.Tensor,
    B: torch.Tensor,
    C: torch.Tensor,
    A_scale: torch.Tensor | None,
    B_scale: torch.Tensor | None,
    topk_weights: torch.Tensor | None,
    sorted_token_ids: torch.Tensor | None,
    expert_ids: torch.Tensor,
    num_tokens_post_padded: torch.Tensor,
    mul_routed_weight: bool,
    top_k: int,
    config: dict[str, Any],
    compute_type: tl.dtype,
    use_fp8_w8a8: bool,
    use_int8_w8a8: bool,
    use_int8_w8a16: bool,
    use_int4_w4a16: bool,
    per_channel_quant: bool,
    block_shape: list[int] | None = None,
    B_bias: torch.Tensor | None = None,
):
    assert topk_weights is not None or not mul_routed_weight
    assert topk_weights is None or topk_weights.stride(1) == 1
    assert sorted_token_ids is None or sorted_token_ids.stride(0) == 1

    if use_fp8_w8a8 or use_int8_w8a8:
        assert B_scale is not None
        assert block_shape is None or triton.cdiv(
            B.size(-2), block_shape[0]
        ) == B_scale.size(-2)
        assert block_shape is None or triton.cdiv(
            B.size(-1), block_shape[1]
        ) == B_scale.size(-1)
    elif use_int8_w8a16 or use_int4_w4a16:
        assert B_scale is not None
        assert block_shape is None or block_shape[0] == 0
    else:
        assert A_scale is None
        assert B_scale is None

    M = A.size(0)
    num_tokens = M * top_k
    if sorted_token_ids is not None:
        EM = sorted_token_ids.size(0)
        if A.size(0) < config["BLOCK_SIZE_M"]:
            # optimize for small batch_size.
            # We assume that top_ids of each token is unique,
            # so num_valid_experts <= batch_size <= BLOCK_SIZE_M,
            # and we can skip some invalid blocks.
            EM = min(
                sorted_token_ids.size(0), A.size(0) * top_k * config["BLOCK_SIZE_M"]
            )
    else:
        EM = num_tokens * config["BLOCK_SIZE_M"]
    grid = lambda META: (
        triton.cdiv(EM, META["BLOCK_SIZE_M"])
        * triton.cdiv(B.size(1), META["BLOCK_SIZE_N"]),
    )
    HAS_BIAS = B_bias is not None

    config = config.copy()
    config["SPLIT_K"] = 1
    BLOCK_SIZE_K = config.pop("BLOCK_SIZE_K")
    if block_shape is not None:
        BLOCK_SIZE_K = min(BLOCK_SIZE_K, min(block_shape[0], block_shape[1]))
    fused_moe_kernel[grid](
        A,
        B,
        C,
        B_bias,
        A_scale,
        B_scale,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        B.size(1),
        B.size(2),
        EM,
        num_tokens,
        A.stride(0),
        A.stride(1),
        B.stride(0),
        B.stride(2),
        B.stride(1),
        C.stride(1),
        C.stride(2),
        A_scale.stride(0) if A_scale is not None and A_scale.ndim == 2 else 0,
        A_scale.stride(1) if A_scale is not None and A_scale.ndim == 2 else 0,
        B_scale.stride(0) if B_scale is not None and B_scale.ndim >= 2 else 0,
        B_scale.stride(2) if B_scale is not None and B_scale.ndim == 3 else 0,
        B_scale.stride(1) if B_scale is not None and B_scale.ndim >= 2 else 0,
        B_bias.stride(0) if B_bias is not None else 0,
        B_bias.stride(1) if B_bias is not None else 0,
        0 if block_shape is None else block_shape[0],
        0 if block_shape is None else block_shape[1],
        MUL_ROUTED_WEIGHT=mul_routed_weight,
        top_k=top_k,
        compute_type=compute_type,
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        per_channel_quant=per_channel_quant,
        naive_block_assignment=(sorted_token_ids is None),
        HAS_BIAS=HAS_BIAS,
        BLOCK_SIZE_K=BLOCK_SIZE_K,
        **config,
    )