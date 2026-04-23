def batched_fused_marlin_moe(
    hidden_states: torch.Tensor,
    expert_num_tokens: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    bias1: torch.Tensor | None,
    bias2: torch.Tensor | None,
    w1_scale: torch.Tensor,
    w2_scale: torch.Tensor,
    quant_type_id: int,
    apply_router_weight_on_input: bool = False,
    global_num_experts: int = -1,
    activation: MoEActivation = MoEActivation.SILU,
    expert_map: torch.Tensor | None = None,
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
    is_k_full: bool = True,
    output: torch.Tensor | None = None,
    inplace: bool = False,
) -> torch.Tensor:
    """
    This function massages the inputs so the batched hidden_states can be
    presented as a 2D contiguous tensor that could be used with
    _fused_marlin_moe.

    Note that both batched_fused_marlin_moe and fused_marlin_moe ultimately
    use `ops.moe_wna16_marlin_gemm` for the gemm operation and
    `ops.moe_mna16_marlin_gemm` supports only 2D contiguous hidden_states.
    Note that the moe_align_block_size function indicates,
        - What rows of the A matrix (hidden_states) to access during the
        matmul, via sorted_ids output.
        - What expert_id to use for each block matmul, via expert_ids output.

    In the batched version, the tokens are already grouped/batched by experts
    they subscribe to. Due to this, we can represent the batched hidden_states
    tensor of shape [B, MAX_TOKENS_PER_BATCH, K] as a 2D tensor of shape,
    [B * MAX_TOKENS_PER_BATCH, K]. We may treat this a 2D contiguous tensor
    with topk=1 as each token (row in the tensor) subscribes to exactly one
    expert_id (which is the batch_id). With the expert_num_tokens tensor, that
    indicates how many tokens are actually valid in each batch, the
    batched_moe_align_block_size function constructs the sorted_ids and
    expert_ids tensors, so only relevant/valid rows of A (hidden_states)
    are accessed and are processed with the correct expert_ids.
    """

    assert hidden_states.ndim == 3, (
        f"hidden states must be batched. e.g. [B, MAX_TOKENS, K]."
        f"But got {hidden_states.size()}"
    )
    if inplace:
        assert output is None, "Conflicting request."

    quant_type = ScalarType.from_id(quant_type_id)
    assert quant_type in [
        scalar_types.uint4,
        scalar_types.uint8b128,
        scalar_types.uint4b8,
        scalar_types.float8_e4m3fn,
        scalar_types.float4_e2m1f,
    ]

    bit4_scalar_types = [
        scalar_types.uint4,
        scalar_types.uint4b8,
        scalar_types.float4_e2m1f,
    ]
    num_bits = 4 if quant_type in bit4_scalar_types else 8

    B, BATCH_TOKENS_MAX, K = hidden_states.size()
    M = hidden_states.view(-1, K).size(0)
    E = w1.size(0)

    # Check constraints.
    assert hidden_states.is_contiguous(), "Hidden_states must be contiguous"
    assert hidden_states.dtype in [torch.float16, torch.bfloat16]
    assert expert_num_tokens.size(0) == E
    assert B == E, (
        "Batch must be as big as number of experts as the tokens"
        "are sorted into the batch/expert they belong to"
    )
    assert w1.size(1) * 16 == K, "Hidden size mismatch w1"
    assert w2.size(2) // (num_bits // 2) == K, "Hidden size mismatch w2"
    assert w1.is_contiguous(), "Expert weights1 must be contiguous"
    assert w2.is_contiguous(), "Expert weights2 must be contiguous"
    assert num_bits in [4, 8]

    # Technically, the tokens are already separated by their expert ids.
    # Hidden-States can just be squeezed to have just 2 dimensions,
    # [B * MAX_TOKENS, K] and top_k can be interpreted as just 1.
    topk = 1

    # TODO(varun) : Choose a decent block size like in fused_marlin_moe
    block_size_m = 64

    sorted_token_ids, expert_ids, num_tokens_post_padded = batched_moe_align_block_size(
        max_tokens_per_batch=BATCH_TOKENS_MAX,
        block_size=block_size_m,
        expert_num_tokens=expert_num_tokens,
    )

    if output is None and inplace:
        output = hidden_states

    # TODO (varun): This can be avoided by plumbing the marlin kernel to
    # ignore topk_weights when topk_weights_ptr is a nullptr.
    topk_weights = torch.ones(
        (M, topk), device=hidden_states.device, dtype=torch.float32
    )

    assert activation is not None
    output = _fused_marlin_moe(
        hidden_states=hidden_states.view(-1, K),
        w1=w1,
        w2=w2,
        bias1=bias1,
        bias2=bias2,
        w1_scale=w1_scale,
        w2_scale=w2_scale,
        topk_weights=topk_weights,
        num_topk=topk,
        quant_type=quant_type,
        apply_router_weight_on_input=apply_router_weight_on_input,
        activation=activation,
        expert_map=expert_map,
        block_size_m=block_size_m,
        sorted_token_ids=sorted_token_ids,
        expert_ids=expert_ids,
        num_tokens_post_padded=num_tokens_post_padded,
        global_scale1=global_scale1,
        global_scale2=global_scale2,
        g_idx1=g_idx1,
        g_idx2=g_idx2,
        sort_indices1=sort_indices1,
        sort_indices2=sort_indices2,
        w1_zeros=w1_zeros,
        w2_zeros=w2_zeros,
        workspace=workspace,
        intermediate_cache13=intermediate_cache13,
        intermediate_cache2=intermediate_cache2,
        output=output.view(-1, K) if output is not None else output,
        is_k_full=is_k_full,
    )

    output = output.view(B, BATCH_TOKENS_MAX, K)

    return output