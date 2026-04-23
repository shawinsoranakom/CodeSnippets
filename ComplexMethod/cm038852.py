def _fused_moe_lora(
    output: torch.Tensor,  # (num_tokens, top_k_num, N*len(lora_a_stacked),)
    qcurr_hidden_states: torch.Tensor,  # (num_tokens, K,)
    lora_a_stacked: list[
        torch.Tensor
    ],  # [(max_loras, num_experts, max_lora_rank, K,),...]
    lora_b_stacked: list[
        torch.Tensor
    ],  # [(max_loras, num_experts, N, max_lora_rank,),...]
    topk_weights: torch.Tensor,  # (num_tokens, top_k_num)
    sorted_token_ids: torch.Tensor | None,  # (max_loras, _)
    expert_ids: torch.Tensor,  # (max_loras, _ ,) or (num_tokens * top_k,)
    num_tokens_post_padded: torch.Tensor | None,  # (max_loras, )
    token_lora_mapping: torch.Tensor,
    max_lora_rank: int,
    top_k_num: int,
    lora_ids: torch.Tensor,
    num_active_loras: torch.Tensor,  # CPU tensor [1], number of active LoRAs
    adapter_enabled: torch.Tensor,
    shrink_block_size_m: int,
    shrink_block_size_n: int,
    shrink_block_size_k: int,
    shrink_group_size_m: int,
    shrink_num_warps: int,
    shrink_num_stages: int,
    shrink_split_k: int,
    expand_block_size_m: int,
    expand_block_size_n: int,
    expand_block_size_k: int,
    expand_group_size_m: int,
    expand_num_warps: int,
    expand_num_stages: int,
    expand_split_k: int,
    mul_routed_weight: bool = False,
    fully_sharded: bool = False,
    offset: int = 0,
) -> None:
    assert len(lora_a_stacked) == len(lora_b_stacked) > 0
    assert topk_weights.dim() == qcurr_hidden_states.dim() == 2
    if sorted_token_ids is None:
        assert expert_ids.dim() == 1
    else:
        assert sorted_token_ids is not None
        assert num_tokens_post_padded is not None
        assert (
            sorted_token_ids.dim()
            == expert_ids.dim()
            == topk_weights.dim()
            == qcurr_hidden_states.dim()
            == 2
        )
        assert (
            sorted_token_ids.shape[0]
            == expert_ids.shape[0]
            == num_tokens_post_padded.shape[0]
        )
    assert output.shape[0] == topk_weights.shape[0]
    assert top_k_num == topk_weights.shape[1]
    device = qcurr_hidden_states.device
    num_slices = len(lora_a_stacked)
    w1_lora_b_stacked = lora_b_stacked[0]
    num_experts = lora_a_stacked[0].shape[1]
    N = max_lora_rank
    M = topk_weights.shape[0]
    K = qcurr_hidden_states.shape[1]
    num_tokens = M * top_k_num
    w1_output_dim_size = w1_lora_b_stacked.shape[2]
    assert shrink_block_size_m == expand_block_size_m
    EM = (
        sorted_token_ids.shape[1]
        if sorted_token_ids is not None
        else num_tokens * shrink_block_size_m
    )

    # TMA is not currently compatiple with fully_sharded due to the non-determinism
    # of token id sorting across ranks.
    use_tma = supports_tma(device) and not fully_sharded

    intermediate_cache_shape = (
        num_slices,
        M,
        top_k_num,
        max_lora_rank,
    )
    if use_tma:
        if num_slices > 1:
            # if num_slices > 1, we construct TMA descriptors for LoRA
            # weights within the kernel, which requires us to first set an allocator
            set_triton_allocator(device)

        # When storing intermediate data in sorted order for TMA, we
        # need an extra 'num_active_loras' dim in the cache to avoid conflicts
        if sorted_token_ids is not None:
            intermediate_cache_shape = (
                num_slices,
                sorted_token_ids.shape[0],
                EM,
                max_lora_rank,
            )

    a_intermediate_cache1 = torch.zeros(
        intermediate_cache_shape,
        dtype=output.dtype,
        device=device,
    )

    use_gdc = supports_pdl(device) and not fully_sharded
    _fused_moe_lora_shrink(
        a_intermediate_cache1,
        qcurr_hidden_states,
        lora_a_stacked,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        token_lora_mapping,
        top_k_num,
        lora_ids,
        adapter_enabled,
        ## adding for kernel
        device,
        N,
        M,
        EM,
        K,
        num_tokens,
        num_experts,
        num_slices,
        shrink_block_size_m,
        shrink_block_size_n,
        shrink_block_size_k,
        shrink_group_size_m,
        shrink_num_warps,
        shrink_num_stages,
        shrink_split_k,
        num_active_loras,
        mul_routed_weight,
        use_gdc=use_gdc,
        use_tma=use_tma,
    )

    if fully_sharded:
        if max_lora_rank == w1_lora_b_stacked.shape[-1]:
            a_intermediate_cache1 = tensor_model_parallel_all_reduce(
                a_intermediate_cache1
            )
        else:
            a_intermediate_cache1 = tensor_model_parallel_all_gather(
                a_intermediate_cache1
            )

            # reset max_lora_rank to the full rank after allgather
            max_lora_rank = a_intermediate_cache1.shape[-1]

    _fused_moe_lora_expand(
        output,
        a_intermediate_cache1,
        lora_b_stacked,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        token_lora_mapping,
        top_k_num,
        lora_ids,
        adapter_enabled,
        ## adding for kernel
        device,
        N,
        M,
        EM,
        K,
        num_tokens,
        num_experts,
        num_slices,
        max_lora_rank,
        w1_output_dim_size,
        expand_block_size_m,
        expand_block_size_n,
        expand_block_size_k,
        expand_group_size_m,
        expand_num_warps,
        expand_num_stages,
        expand_split_k,
        num_active_loras,
        mul_routed_weight,
        offset,
        use_gdc=use_gdc,
        use_tma=use_tma,
    )