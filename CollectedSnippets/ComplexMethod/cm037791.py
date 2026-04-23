def run_cutlass_moe_w4a8_fp8(
    output: torch.Tensor,
    hidden_states: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    topk_ids: torch.Tensor,
    activation: MoEActivation,
    global_num_experts: int,
    expert_map: torch.Tensor | None,
    w1_scale: torch.Tensor | None,
    w2_scale: torch.Tensor | None,
    a1q_scale: torch.Tensor | None,
    a2_scale: torch.Tensor | None,
    w1_chan_scale: torch.Tensor,
    w2_chan_scale: torch.Tensor,
    a_strides1: torch.Tensor,
    a_strides2: torch.Tensor,
    b_strides1: torch.Tensor,
    b_strides2: torch.Tensor,
    c_strides1: torch.Tensor,
    c_strides2: torch.Tensor,
    s_strides1: torch.Tensor,
    s_strides2: torch.Tensor,
    workspace13: torch.Tensor,
    workspace2: torch.Tensor,
    expert_num_tokens: torch.Tensor | None,
    out_dtype: torch.dtype,
    per_act_token: bool,
    per_out_ch: bool,
    use_batched_format: bool,
    topk_weights: torch.Tensor | None,
    group_size: int,
):
    a1q = hidden_states
    M = a1q.size(0)
    local_E = w1.size(0)
    device = a1q.device
    _, K, N_packed = w2.shape
    N = N_packed * 8  # logical N, pack 8 int4 into 1 int32

    assert per_act_token, "W4A8 must use per-token scales"
    assert per_out_ch, "W4A8 must use per-channel scales"
    assert w1_scale is not None
    assert w2_scale is not None
    assert w1_scale.dtype == torch.float8_e4m3fn
    assert w2_scale.dtype == torch.float8_e4m3fn
    assert w1.dtype == torch.int32
    assert w2.dtype == torch.int32
    assert w1_chan_scale.dtype == torch.float32
    assert w2_chan_scale.dtype == torch.float32
    assert w1.size(0) == w2.size(0), "Weights expert number mismatch"
    assert a1q_scale is not None
    assert a2_scale is None
    assert out_dtype in [torch.bfloat16], f"Invalid output dtype: {out_dtype}"
    if expert_map is not None:
        assert expert_num_tokens is None
    assert not use_batched_format, "batched format not supported yet"
    assert group_size == 128, f"Only group size 128 supported but got {group_size=}"

    assert global_num_experts != -1
    assert w1.size(2) * 8 == K, (
        f"w1 hidden size mismatch: got {w1.size(2) * 8}, expected {K=}"
    )

    topk = topk_ids.size(1)
    a1q_perm = _resize_cache(workspace2.view(dtype=torch.float8_e4m3fn), (M * topk, K))
    mm1_out = _resize_cache(workspace13, (M * topk, N * 2))
    act_out = _resize_cache(workspace2, (M * topk, N))
    # original workspace are based on input hidden_states dtype (bf16)
    quant_out = _resize_cache(
        workspace13.view(dtype=torch.float8_e4m3fn), (M * topk, N)
    )
    mm2_out = _resize_cache(workspace2, (M * topk, K))

    problem_sizes1 = torch.empty((local_E, 3), dtype=torch.int32, device=device)
    problem_sizes2 = torch.empty((local_E, 3), dtype=torch.int32, device=device)

    num_expert = global_num_experts if expert_map is None else expert_map.size(0)
    # permuted a1q reuses workspace2
    a1q, a1q_scale, expert_first_token_offset, inv_perm, _ = moe_permute(
        a1q,
        a1q_scale,
        topk_ids,
        num_expert,
        local_E,
        expert_map,
        permuted_hidden_states=a1q_perm,
    )
    # for RS gemm SwapAB is always enabled (swap logical M, N in the problem shape).
    ops.get_cutlass_moe_mm_problem_sizes_from_expert_offsets(
        expert_first_token_offset, problem_sizes1, problem_sizes2, N, K, True
    )
    expert_offsets = expert_first_token_offset[:-1]

    ops.cutlass_w4a8_moe_mm(
        mm1_out,
        a1q,
        w1,
        a1q_scale,
        w1_chan_scale,
        w1_scale,
        group_size,
        expert_offsets,
        problem_sizes1,
        a_strides1,
        b_strides1,
        c_strides1,
        s_strides1,
    )

    apply_moe_activation(activation, act_out, mm1_out)

    a2q, a2q_scale = ops.scaled_fp8_quant(
        act_out, a2_scale, use_per_token_if_dynamic=per_act_token, output=quant_out
    )

    ops.cutlass_w4a8_moe_mm(
        mm2_out,
        a2q,
        w2,
        a2q_scale,
        w2_chan_scale,
        w2_scale,
        group_size,
        expert_offsets,
        problem_sizes2,
        a_strides2,
        b_strides2,
        c_strides2,
        s_strides2,
    )

    # for non-chunking mode the output is resized from workspace13
    # so we need to make sure mm2_out uses workspace2.
    moe_unpermute(
        out=output,
        permuted_hidden_states=mm2_out,
        topk_weights=topk_weights,
        inv_permuted_idx=inv_perm,
        expert_first_token_offset=expert_first_token_offset,
    )