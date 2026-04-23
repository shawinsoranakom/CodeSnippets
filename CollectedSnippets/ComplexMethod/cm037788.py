def run_cutlass_moe_fp8(
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
    ab_strides1: torch.Tensor,
    ab_strides2: torch.Tensor,
    c_strides1: torch.Tensor,
    c_strides2: torch.Tensor,
    workspace13: torch.Tensor,
    workspace2: torch.Tensor,
    expert_num_tokens: torch.Tensor | None,
    out_dtype: torch.dtype,
    per_act_token: bool,
    per_out_ch: bool,
    use_batched_format: bool,
    topk_weights: torch.Tensor | None,
):
    a1q = hidden_states

    assert activation.is_gated, "Only gated activation is supported"
    assert w1_scale is not None
    assert w2_scale is not None
    assert w1.dtype == torch.float8_e4m3fn
    assert w2.dtype == torch.float8_e4m3fn
    assert a1q.size(-1) == w1.size(2), "Hidden size mismatch w1"
    assert w1.size(1) == w2.size(2) * 2, "Hidden size mismatch w2"
    assert (
        w1_scale.dim() == 1 or w1_scale.size(1) == 1 or w1_scale.shape[1] == w1.size(1)
    ), "W1 scale shape mismatch"
    assert (
        w2_scale.dim() == 1 or w2_scale.size(1) == 1 or w2_scale.shape[1] == w2.size(1)
    ), "W2 scale shape mismatch"
    assert w1.size(0) == w2.size(0), "Expert number mismatch"
    assert (
        a1q_scale is None
        or a1q_scale.dim() == 0
        or a1q_scale.size(0) == 1
        or a1q_scale.size(0) == a1q.shape[0]
    ), "Input scale shape mismatch"
    assert w1.size(0) == w2.size(0), "Weights expert number mismatch"
    assert w1.size(0) == w1_scale.size(0), "w1 scales expert number mismatch"
    assert w1.size(0) == w2_scale.size(0), "w2 scales expert number mismatch"
    assert (
        a2_scale is None
        or a2_scale.dim() == 0
        or a2_scale.size(0) == 1
        or a2_scale.size(0) == a1q.shape[0]
    ), "Intermediate scale shape mismatch"
    assert out_dtype in [torch.half, torch.bfloat16], "Invalid output dtype"

    # NOTE(rob): the expert_map is used for the STANDARD case and
    # the batched format is used by the BATCHED case.
    # TODO(rob): update the MK interface to only pass the expert_map
    # during the STANDARD case to make this clearer across all kernels.
    if use_batched_format:
        assert expert_num_tokens is not None
    else:
        assert expert_num_tokens is None

    # We have two modes: batched experts and non-batched experts.
    # In the non-batched mode, the input tokens are not padded: thus, the shape
    # of the input is [total_num_tokens, hidden_size]. The input and output
    # require shuffling by a_map and c_map such that the tokens assigned to
    # each expert are contiguous.
    # In the batched mode, the input tokens are padded per expert to ensure that
    # the batched dispatch and combine functions work correctly: thus, the shape
    # of the input is [num_experts, max_num_tokens_per_expert, hidden_size].
    # The batched input and output require no shuffling by a_map and c_map since
    # their tokens are already contiguous for each expert as a result of
    # the dispatch function.

    M = a1q.size(0)  # non batched expert M
    padded_M = a1q.size(1)  # batched expert M
    _, K, N = w2.shape
    device = a1q.device

    assert w1.size(2) == K
    assert global_num_experts != -1
    assert a1q_scale is not None

    topk = topk_ids.size(1)
    local_E = w1.size(0)

    if use_batched_format:
        mm1_out = _resize_cache(workspace13, (local_E * padded_M, N * 2))
        act_out = _resize_cache(workspace2, (local_E * padded_M, N))
        quant_out = _resize_cache(
            workspace13.view(dtype=torch.float8_e4m3fn), (local_E * padded_M, N)
        )
        mm2_out = _resize_cache(workspace2, (local_E * padded_M, K))
    else:
        a1q_perm = _resize_cache(
            workspace2.view(dtype=torch.float8_e4m3fn), (M * topk, K)
        )
        mm1_out = _resize_cache(workspace13, (M * topk, N * 2))
        act_out = _resize_cache(workspace2, (M * topk, N))
        # original workspace are based on input hidden_states dtype (bf16)
        quant_out = _resize_cache(
            workspace13.view(dtype=torch.float8_e4m3fn), (M * topk, N)
        )
        mm2_out = _resize_cache(workspace2, (M * topk, K))

    if use_batched_format:
        assert expert_num_tokens is not None

        expert_offsets = torch.empty((local_E), dtype=torch.int32, device=device)
        problem_sizes1 = torch.empty((local_E, 3), dtype=torch.int32, device=device)
        problem_sizes2 = torch.empty((local_E, 3), dtype=torch.int32, device=device)

        ops.get_cutlass_batched_moe_mm_data(
            expert_offsets,
            problem_sizes1,
            problem_sizes2,
            expert_num_tokens,
            local_E,
            padded_M,
            N,
            K,
        )

        w1_scale = w1_scale.reshape(w1_scale.size(0), -1)
        w2_scale = w2_scale.reshape(w2_scale.size(0), -1)
        a1q = a1q.reshape(-1, a1q.size(2))
        a1q_scale = a1q_scale.reshape(-1, a1q_scale.size(2)).contiguous()
        # c3x get_group_gemm_starts expects int64 to avoid overflow
        # during offset calculations
        expert_offsets = expert_offsets.to(torch.int64)
    else:
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
        # swap_ab is a CUTLASS grouped-GEMM optimization (M <= 64 reduces padding).
        swap_ab = a1q.size(0) <= 64
        ops.get_cutlass_moe_mm_problem_sizes_from_expert_offsets(
            expert_first_token_offset, problem_sizes1, problem_sizes2, N, K, swap_ab
        )
        expert_offsets = expert_first_token_offset[:-1]

    if not per_act_token and (expert_map is not None or use_batched_format):
        # this is necessary to avoid imprecise scale calculation caused by
        # random data in the unused workspace. The workspace is unused when
        # this rank handles only partial tokens, or when it is batched .
        mm1_out.fill_(0)

    ops.cutlass_moe_mm(
        mm1_out,
        a1q,
        w1,
        a1q_scale,
        w1_scale,
        expert_offsets,
        problem_sizes1,
        ab_strides1,
        ab_strides1,
        c_strides1,
        per_act_token,
        per_out_ch,
    )

    apply_moe_activation(activation, act_out, mm1_out)

    a2q, a2q_scale = ops.scaled_fp8_quant(
        act_out, a2_scale, use_per_token_if_dynamic=per_act_token, output=quant_out
    )

    ops.cutlass_moe_mm(
        mm2_out,
        a2q,
        w2,
        a2q_scale,
        w2_scale,
        expert_offsets,
        problem_sizes2,
        ab_strides2,
        ab_strides2,
        c_strides2,
        per_act_token,
        per_out_ch,
    )

    if use_batched_format:
        output.copy_(mm2_out.reshape(local_E, padded_M, K), non_blocking=True)
    else:
        # for non-chunking mode the output is resized from workspace13
        # so we need to make sure mm2_out uses workspace2.
        moe_unpermute(
            out=output,
            permuted_hidden_states=mm2_out,
            topk_weights=topk_weights,
            inv_permuted_idx=inv_perm,
            expert_first_token_offset=expert_first_token_offset,
        )