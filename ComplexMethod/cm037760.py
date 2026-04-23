def dispatch_fused_moe_kernel(
    A: torch.Tensor,
    B: torch.Tensor,
    C: torch.Tensor,
    A_scale: torch.Tensor | None,
    B_scale: torch.Tensor | None,
    B_zp: torch.Tensor | None,
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
) -> None:
    assert topk_weights is not None or not mul_routed_weight
    assert topk_weights is None or topk_weights.stride(1) == 1
    assert sorted_token_ids is None or sorted_token_ids.stride(0) == 1

    M = A.size(0)
    num_tokens = M * top_k

    if (use_int8_w8a16 or use_int4_w4a16) and (
        block_shape is not None and block_shape[1] > 0
    ):
        assert B_bias is None

        use_moe_wna16_cuda = should_moe_wna16_use_cuda(
            num_valid_tokens=num_tokens,
            group_size=block_shape[1],
            num_experts=B.size(0),
            bit=4 if use_int4_w4a16 else 8,
        )

        if use_moe_wna16_cuda:
            invoke_fused_moe_wna16_cuda_kernel(
                A,
                B,
                C,
                B_scale,
                B_zp,
                topk_weights,
                sorted_token_ids,
                expert_ids,
                num_tokens_post_padded,
                mul_routed_weight,
                top_k,
                config,
                block_shape,
            )
            return
        invoke_fused_moe_wna16_triton_kernel(
            A,
            B,
            C,
            B_scale,
            B_zp,
            topk_weights,
            sorted_token_ids,
            expert_ids,
            num_tokens_post_padded,
            mul_routed_weight,
            top_k,
            config,
            compute_type,
            use_int8_w8a16,
            use_int4_w4a16,
            block_shape,
        )

    else:
        invoke_fused_moe_triton_kernel(
            A,
            B,
            C,
            A_scale,
            B_scale,
            topk_weights,
            sorted_token_ids,
            expert_ids,
            num_tokens_post_padded,
            mul_routed_weight,
            top_k,
            config,
            compute_type,
            use_fp8_w8a8,
            use_int8_w8a8,
            use_int8_w8a16,
            use_int4_w4a16,
            per_channel_quant,
            block_shape,
            B_bias,
        )