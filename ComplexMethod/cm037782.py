def _fused_marlin_moe(
    hidden_states: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    bias1: torch.Tensor | None,
    bias2: torch.Tensor | None,
    w1_scale: torch.Tensor,
    w2_scale: torch.Tensor,
    topk_weights: torch.Tensor,
    num_topk: int,
    quant_type: ScalarType,
    apply_router_weight_on_input: bool,
    expert_map: torch.Tensor | None,
    block_size_m: int,
    sorted_token_ids: torch.Tensor,
    expert_ids: torch.Tensor,
    num_tokens_post_padded: torch.Tensor,
    activation: MoEActivation = MoEActivation.SILU,
    activation_func: Callable[
        [MoEActivation, torch.Tensor, torch.Tensor], None
    ] = apply_moe_activation,
    input_global_scale1: torch.Tensor | None = None,
    input_global_scale2: torch.Tensor | None = None,
    global_scale1: torch.Tensor | None = None,
    global_scale2: torch.Tensor | None = None,
    g_idx1: torch.Tensor | None = None,
    g_idx2: torch.Tensor | None = None,
    sort_indices1: torch.Tensor | None = None,
    sort_indices2: torch.Tensor | None = None,
    w1_zeros: torch.Tensor | None = None,
    w2_zeros: torch.Tensor | None = None,
    workspace: torch.Tensor | None = None,
    intermediate_cache13: torch.Tensor | None = None,
    intermediate_cache2: torch.Tensor | None = None,
    output: torch.Tensor | None = None,
    input_dtype: torch.dtype | None = None,
    is_k_full: bool = True,
) -> torch.Tensor:
    assert hidden_states.ndim == 2
    M, K = hidden_states.size()
    N = marlin_moe_intermediate_size(w1, w2)
    w13_num_shards = 2 if activation.is_gated else 1
    if workspace is None:
        workspace = marlin_make_workspace_new(hidden_states.device, 4)

    if intermediate_cache13 is None:
        intermediate_cache13 = torch.empty(
            (M * num_topk * max(w13_num_shards * N, K),),
            device=hidden_states.device,
            dtype=hidden_states.dtype,
        )

    if intermediate_cache2 is None:
        intermediate_cache2 = torch.empty(
            (M * num_topk, N),
            device=hidden_states.device,
            dtype=hidden_states.dtype,
        )

    intermediate_cache1 = _resize_cache(
        intermediate_cache13, (M * num_topk, w13_num_shards * N)
    )

    intermediate_cache3 = _resize_cache(intermediate_cache13, (M * num_topk, K))

    intermediate_cache2 = _resize_cache(intermediate_cache2, (M * num_topk, N))

    a_scales1 = None
    gate_up_input = hidden_states
    if input_dtype == torch.int8:
        gate_up_input, a_scales1 = marlin_quant_input(hidden_states, input_dtype)
        if input_global_scale1 is not None:
            a_scales1 = a_scales1 * input_global_scale1
    elif input_dtype == torch.float8_e4m3fn:
        gate_up_input, a_scales1 = marlin_quant_input(hidden_states, input_dtype)

    intermediate_cache1 = ops.moe_wna16_marlin_gemm(
        gate_up_input,
        intermediate_cache1,
        w1,
        bias1,
        w1_scale,
        a_scales1,
        global_scale1,
        w1_zeros,
        g_idx1,
        sort_indices1,
        workspace,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        topk_weights,
        moe_block_size=block_size_m,
        top_k=num_topk,
        mul_topk_weights=apply_router_weight_on_input,
        b_q_type=quant_type,
        size_m=M,
        size_n=w13_num_shards * N,
        size_k=K,
        is_k_full=is_k_full,
        use_atomic_add=False,
        use_fp32_reduce=True,
        is_zp_float=False,
    )
    activation_func(
        activation,
        intermediate_cache2,
        intermediate_cache1.view(-1, w13_num_shards * N),
    )

    if output is None:
        output = intermediate_cache3

    if expert_map is not None:
        output.zero_()

    a_scales2 = None
    if input_dtype == torch.int8:
        intermediate_cache2, a_scales2 = marlin_quant_input(
            intermediate_cache2, input_dtype
        )
        if input_global_scale2 is not None:
            a_scales2 = a_scales2 * input_global_scale2
    elif input_dtype == torch.float8_e4m3fn:
        intermediate_cache2, a_scales2 = marlin_quant_input(
            intermediate_cache2, input_dtype
        )

    output = ops.moe_wna16_marlin_gemm(
        intermediate_cache2,
        output,
        w2,
        bias2,
        w2_scale,
        a_scales2,
        global_scale2,
        w2_zeros,
        g_idx2,
        sort_indices2,
        workspace,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        topk_weights,
        moe_block_size=block_size_m,
        top_k=1,
        mul_topk_weights=not apply_router_weight_on_input,
        b_q_type=quant_type,
        size_m=M * num_topk,
        size_n=K,
        size_k=N,
        is_k_full=is_k_full,
        use_atomic_add=False,
        use_fp32_reduce=True,
        is_zp_float=False,
    )

    return output