def run_cutlass_moe_fp4(
    output: torch.Tensor,
    a: torch.Tensor,
    a1_gscale: torch.Tensor,
    w1_fp4: torch.Tensor,
    w1_blockscale: torch.Tensor,
    w1_alphas: torch.Tensor,
    a2_gscale: torch.Tensor,
    w2_fp4: torch.Tensor,
    w2_blockscale: torch.Tensor,
    w2_alphas: torch.Tensor,
    topk_weights: torch.Tensor,
    topk_ids: torch.Tensor,
    activation: MoEActivation,
    workspace13: torch.Tensor,
    workspace2: torch.Tensor,
    m: int,
    n: int,
    k: int,
    e: int,
    device: torch.device,
    apply_router_weight_on_input: bool = False,
) -> None:
    """
    MoE implementation for FP4 Inputs

    # Gemm 1
    a: Input tensor: [m, k] (half/bfloat16)
    a1_gscale: Activation scale per expert: [e]  (float32)
    w1 (not an argument to cutlass_moe_fp4): [e, w1_n, k]
    w1_fp4: [e, w1_n, k // 2], dtype: torch.uint8 (stacked fp4: E2M1)
    where w1_n = 2*n for gated activations (gate+up), n for non-gated (up only).
    (Note: `n` is the up projection output dim, `k` is the input dim in
     full precision)
    w1_blockscale: [e, w1_n, k // block_size] (float8_e4m3)
                   (Block size = 16 for NVFP4)

    # Gemm 2
    a2_gscale: Activation scale per expert: [e]
    w2(down projection) (not an argument to cutlass_moe_fp4): [e, k, n]
    w2_fp4: [e, k, n // 2], dtype: torch.uint8 (stacked E2M1)
    w2_blockscale: [e, k, n // block_size], dtype: float8_e4m3

    topk_weights: [m, topk] dtype: float8
    topk_ids: [m, topk] dtype: float8

    m, n, k: Unquantized weight shapes, dtype: int
    e: number of experts, dtype: int

    assumes that topk < k < n to satisfy - up/down projection expectations.
    """
    is_gated = activation.is_gated
    # For gated activations (e.g. SiLU), w1 output is 2*n (gate + up).
    # For non-gated activations (e.g. SiLU_NO_MUL), w1 output is n (up only).
    w1_n = n * 2 if is_gated else n

    assert topk_weights.shape == topk_ids.shape, "topk shape mismatch"
    assert w1_fp4.dtype == torch.uint8, "weight 1 must be uint8"
    assert w2_fp4.dtype == torch.uint8, "weight 2 must be uint8"
    assert (
        w1_fp4.ndim == 3
        and w2_fp4.ndim == 3
        and w1_blockscale.ndim == 3
        and w2_blockscale.ndim == 3
    ), "All Weights must be of rank 3 for cutlass_moe_fp4"
    m_a, k_a = a.shape
    e_w1, w1_n_actual, half_k_w1 = w1_fp4.shape
    e_w2, k_w2, half_n_w2 = w2_fp4.shape

    assert e_w1 == e_w2 and e_w1 == e, (
        "Number of experts must match",
        f" between weights. {e_w1}, {e_w2}, {e}",
    )
    assert k_a == half_k_w1 * 2 and k == k_w2, (
        "Hidden size mismatch between a, w1 and w2"
    )
    assert w1_n_actual == w1_n and half_n_w2 * 2 == n, "mismatch in expected `n`"
    assert m == m_a, "input shape mismatch"
    assert 2 * half_k_w1 == k_w2, "Hidden size mismatch w2 and w1"
    assert a.dtype in [torch.half, torch.bfloat16], "Invalid input dtype"
    assert topk_weights.size(0) == m and topk_ids.size(0) == m, (
        "topk must be provided for each row of a"
    )
    topk = topk_ids.size(1)
    out_dtype = a.dtype
    num_topk = topk_ids.size(1)

    expert_offsets = torch.empty((e + 1), dtype=torch.int32, device=device)
    blockscale_offsets = torch.empty((e + 1), dtype=torch.int32, device=device)
    # Problem size:  (num_experts, (m,2n,k))
    problem_sizes1 = torch.empty((e, 3), dtype=torch.int32, device=device)
    # Problem size:  (num_experts, (m,n,k))
    problem_sizes2 = torch.empty((e, 3), dtype=torch.int32, device=device)

    a_map = torch.empty((topk_ids.numel()), dtype=torch.int32, device=device)
    c_map = torch.empty((topk_ids.numel()), dtype=torch.int32, device=device)

    if apply_router_weight_on_input:
        # TODO: this only works for topK=1, will need to update for topK>1
        assert num_topk == 1, (
            "apply_router_weight_on_input is only implemented for topk=1"
        )
        a.mul_(topk_weights.to(out_dtype))

    # problem shapes should have [m, n, k]
    # Note that problem sizes are based on logical number of elements.
    ops.get_cutlass_moe_mm_data(
        topk_ids,
        expert_offsets,
        problem_sizes1,
        problem_sizes2,
        a_map,
        c_map,
        e,
        n,
        k,
        blockscale_offsets,
        is_gated=is_gated,
    )

    a = ops.shuffle_rows(a, a_map)
    rep_a_fp4, rep_a_blockscale = ops.scaled_fp4_experts_quant(
        a,
        a1_gscale,
        expert_offsets,
        blockscale_offsets,
        num_topk,
    )
    c1 = _resize_cache(workspace13, (m * topk, w1_n))
    c2 = _resize_cache(workspace2, (m * topk, n))
    c3 = _resize_cache(workspace13, (m * topk, k))
    ops.cutlass_fp4_moe_mm(
        c1,
        rep_a_fp4,
        w1_fp4,
        rep_a_blockscale,
        w1_blockscale,
        w1_alphas,
        problem_sizes1,
        expert_offsets[:-1],
        blockscale_offsets[:-1],
    )
    del rep_a_fp4, rep_a_blockscale
    if activation == MoEActivation.SILU:
        # Fused SiLU+Mul+NVFP4 quantization
        # Note: c2 workspace is no longer needed since SiLU is fused with quantization.
        # c3 reuses workspace13 after c1 is consumed.
        int_fp4, int_blockscale = ops.silu_and_mul_scaled_fp4_experts_quant(
            c1, a2_gscale, expert_offsets, blockscale_offsets, num_topk
        )
    else:
        apply_moe_activation(activation, c2, c1)
        int_fp4, int_blockscale = ops.scaled_fp4_experts_quant(
            c2, a2_gscale, expert_offsets, blockscale_offsets, num_topk
        )

    ops.cutlass_fp4_moe_mm(
        c3,
        int_fp4,
        w2_fp4,
        int_blockscale,
        w2_blockscale,
        w2_alphas,
        problem_sizes2,
        expert_offsets[:-1],
        blockscale_offsets[:-1],
    )
    del int_fp4, int_blockscale

    c3 = ops.shuffle_rows(c3, c_map)

    assert output.dtype == out_dtype
    if not apply_router_weight_on_input:
        output.copy_(
            (
                c3.view(m, num_topk, k)
                * topk_weights.view(m, num_topk, 1).to(out_dtype)
            ).sum(dim=1),
            non_blocking=True,
        )
    else:
        output.copy_(c3.view(m, num_topk, k).sum(dim=1), non_blocking=True)
    return