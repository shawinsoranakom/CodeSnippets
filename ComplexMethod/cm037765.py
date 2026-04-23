def fused_experts_impl(
    hidden_states: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    topk_weights: torch.Tensor,
    topk_ids: torch.Tensor,
    inplace: bool,
    activation: str = "silu",
    apply_router_weight_on_input: bool = False,
    use_fp8_w8a8: bool = False,
    use_int8_w8a8: bool = False,
    use_int8_w8a16: bool = False,
    use_int4_w4a16: bool = False,
    ocp_mx_scheme: str | None = None,
    per_channel_quant: bool = False,
    global_num_experts: int = -1,
    expert_map: torch.Tensor | None = None,
    w1_scale: torch.Tensor | None = None,
    w2_scale: torch.Tensor | None = None,
    w1_zp: torch.Tensor | None = None,
    w2_zp: torch.Tensor | None = None,
    a1_scale: torch.Tensor | None = None,
    a2_scale: torch.Tensor | None = None,
    block_shape: list[int] | None = None,
    w1_bias: torch.Tensor | None = None,
    w2_bias: torch.Tensor | None = None,
) -> torch.Tensor:
    if ocp_mx_scheme is not None:
        raise NotImplementedError(
            f"Using ocp_mx_scheme={ocp_mx_scheme} in functional fused_experts call is "
            "deprecated. Please use OCP_MXQuantizationEmulationTritonExperts."
        )

    # Convert string activation to enum for internal use
    activation_enum = MoEActivation.from_str(activation)

    # Check constraints.
    if use_int4_w4a16:
        assert hidden_states.size(1) // 2 == w1.size(2), "Hidden size mismatch"
    else:
        assert hidden_states.size(1) == w1.size(2), (
            f"Hidden size mismatch {hidden_states.size(1)} != {w1.size(2)}"
        )

    assert topk_weights.size() == topk_ids.size(), "topk shape mismatch"
    assert hidden_states.is_contiguous(), "Hidden_states must be contiguous"
    assert w1.stride(-1) == 1, "Stride of last dimension must be 1"
    assert w2.stride(-1) == 1, "Stride of last dimension must be 1"
    assert hidden_states.dtype in [torch.float32, torch.float16, torch.bfloat16]

    num_tokens = hidden_states.size(0)
    E, N, _ = w1.size()
    K = w2.size(1)
    if global_num_experts == -1:
        global_num_experts = E
    top_k_num = topk_ids.size(1)

    M = num_tokens

    config_dtype = _get_config_dtype_str(
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        use_int4_w4a16=use_int4_w4a16,
        dtype=hidden_states.dtype,
    )

    # Note: for use_int8_w8a16 or use_int4_w4a16, the activations are
    # quantized prior to calling fused_experts.
    quant_dtype = _get_config_quant_dtype(
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        ocp_mx_scheme=None,
    )

    get_config_func = functools.partial(
        try_get_optimal_moe_config,
        w1.size(),
        w2.size(),
        top_k_num,
        config_dtype,
        block_shape=block_shape,
    )

    config = get_config_func(M)

    # We can reuse the memory between these because by the time we need
    # cache3, we're done with cache1
    cache13 = torch.empty(
        M * top_k_num * max(N, K),
        device=hidden_states.device,
        dtype=hidden_states.dtype,
    )
    intermediate_cache1 = cache13[: M * top_k_num * N].view(M, top_k_num, N)
    intermediate_cache3 = cache13[: M * top_k_num * K].view(M, top_k_num, K)

    # This needs separate memory since it's used concurrently with cache1
    activation_out_dim = mk.FusedMoEExpertsModular.adjust_N_for_activation(
        N, activation_enum
    )
    intermediate_cache2 = torch.empty(
        (M * top_k_num, activation_out_dim),
        device=hidden_states.device,
        dtype=hidden_states.dtype,
    )

    if hidden_states.dtype == torch.bfloat16:
        compute_type = tl.bfloat16
    elif hidden_states.dtype == torch.float16:
        compute_type = tl.float16
    elif hidden_states.dtype == torch.float32:
        compute_type = tl.float32
    else:
        raise ValueError(f"Unsupported compute_type: {hidden_states.dtype}")

    out_hidden_states = hidden_states if inplace else torch.empty_like(hidden_states)

    qhidden_states, a1q_scale = moe_kernel_quantize_input(
        A=hidden_states,
        A_scale=a1_scale,
        quant_dtype=quant_dtype,
        per_act_token_quant=per_channel_quant,
        block_shape=block_shape,
    )

    sorted_token_ids, expert_ids, num_tokens_post_padded = _prepare_expert_assignment(
        topk_ids,
        config,
        num_tokens,
        top_k_num,
        global_num_experts,
        expert_map,
        use_int8_w8a16=use_int8_w8a16,
        use_int4_w4a16=use_int4_w4a16,
        block_shape=block_shape,
        ignore_invalid_experts=True,
    )

    dispatch_fused_moe_kernel(
        qhidden_states,
        w1,
        intermediate_cache1,
        a1q_scale,
        w1_scale,
        w1_zp,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        apply_router_weight_on_input,
        top_k_num,
        config,
        compute_type=compute_type,
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        use_int4_w4a16=use_int4_w4a16,
        per_channel_quant=per_channel_quant,
        block_shape=block_shape,
        B_bias=w1_bias,
    )

    apply_moe_activation(
        activation_enum, intermediate_cache2, intermediate_cache1.view(-1, N)
    )

    qintermediate_cache2, a2q_scale = moe_kernel_quantize_input(
        A=intermediate_cache2,
        A_scale=a2_scale,
        quant_dtype=quant_dtype,
        per_act_token_quant=per_channel_quant,
        block_shape=block_shape,
    )

    if expert_map is not None:
        intermediate_cache3.zero_()

    dispatch_fused_moe_kernel(
        qintermediate_cache2,
        w2,
        intermediate_cache3,
        a2q_scale,
        w2_scale,
        w2_zp,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        not apply_router_weight_on_input,
        1,
        config,
        compute_type=compute_type,
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        use_int4_w4a16=use_int4_w4a16,
        per_channel_quant=per_channel_quant,
        block_shape=block_shape,
        B_bias=w2_bias,
    )

    ops.moe_sum(
        intermediate_cache3.view(*intermediate_cache3.size()),
        out_hidden_states,
    )

    return out_hidden_states