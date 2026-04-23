def _fused_moe_lora_shrink_fp8(
    a_intermediate_cache1: torch.Tensor,
    # (num_slices, num_tokens, top_k_num, max_lora_rank)
    qcurr_hidden_states: torch.Tensor,  # (num_tokens, K,)
    lora_a_stacked: list[
        torch.Tensor
    ],  # [(max_loras, num_experts, max_lora_rank, K,),...]
    topk_weights: torch.Tensor,  # (num_tokens, top_k_num)
    sorted_token_ids: torch.Tensor | None,  # (max_loras, _)
    expert_ids: torch.Tensor,  # (max_loras, _ ,) or (num_tokens * top_k,)
    num_tokens_post_padded: torch.Tensor | None,  # (max_loras, )
    token_lora_mapping: torch.Tensor,
    top_k_num: int,
    lora_ids: torch.Tensor,
    adapter_enabled: torch.Tensor,
    ## adding for kernel
    device: torch.device,
    N: int,
    M: int,
    EM: int,
    K: int,
    num_tokens: int,
    num_experts: int,
    num_slices: int,
    block_size_m: int,
    block_size_n: int,
    block_size_k: int,
    group_size_m: int,
    num_warps: int,
    num_stages: int,
    split_k: int,
    num_active_loras: int,
    lora_a_scale_stacked: list[torch.Tensor],
    mul_routed_weight: bool = False,
    use_gdc: bool = False,
    act_scale: torch.Tensor | None = None,
    use_fp8_w8a8: bool = False,
    use_int8_w8a8: bool = False,
    use_int8_w8a16: bool = False,
    per_channel_quant: bool = False,
    block_shape: List[int] | None = None,  # noqa: UP006, UP007
) -> None:
    if use_fp8_w8a8 or use_int8_w8a8:
        assert lora_a_scale_stacked is not None, (
            "lora_a_scale_stacked must be provided for w8a8 quantization"
        )
        assert block_shape is None or triton.cdiv(
            lora_a_stacked[0].size(-2), block_shape[0]
        ) == lora_a_scale_stacked[0].size(-2), (
            "Incompatible block shape for lora_a_scale_stacked.size(-2) "
        )
        assert block_shape is None or triton.cdiv(
            lora_a_stacked[0].size(-1), block_shape[1]
        ) == lora_a_scale_stacked[0].size(-1), (
            "Incompatible block shape for lora_a_scale_stacked.size(-1) "
        )
    elif use_int8_w8a16:
        assert lora_a_scale_stacked is not None, (
            "lora_a_scale_stacked must be provided for w8a16 quantization"
        )
        assert block_shape is None or block_shape[0] == 0, (
            "Block shape for activation must be 0 for w8a16"
        )
    else:
        assert act_scale is None
        assert lora_a_scale_stacked is None

    if block_shape is not None:
        block_size_k = min(block_size_k, min(block_shape[0], block_shape[1]))

    if lora_a_scale_stacked is not None:
        b_scale_ptr = _get_ptr(lora_a_scale_stacked, device)
        w1_lora_a_scale_stacked = lora_a_scale_stacked[0]

    w1_lora_a_stacked = lora_a_stacked[0]
    shrink_config = {
        "BLOCK_SIZE_M": block_size_m,
        "BLOCK_SIZE_N": block_size_n,
        "BLOCK_SIZE_K": block_size_k,
        "GROUP_SIZE_M": group_size_m,
        "num_warps": num_warps,
        "num_stages": num_stages,
        "SPLIT_K": split_k,
        "USE_GDC": use_gdc,
        "launch_pdl": use_gdc,  # triton kernel metadata
    }

    b_ptr = _get_ptr(lora_a_stacked, device)

    grid_lora_dim, stride_tl, stride_el = _adjust_kernel_inputs(
        num_active_loras, sorted_token_ids, expert_ids
    )

    grid = lambda META: (
        split_k
        * triton.cdiv(EM, META["BLOCK_SIZE_M"])
        * triton.cdiv(N, META["BLOCK_SIZE_N"]),
        len(lora_a_stacked),
        grid_lora_dim,
    )
    _fused_moe_lora_kernel_fp8[grid](
        qcurr_hidden_states,
        b_ptr,
        a_intermediate_cache1,
        act_scale,
        b_scale_ptr if lora_a_scale_stacked is not None else None,
        topk_weights,
        sorted_token_ids,
        expert_ids,
        num_tokens_post_padded,
        token_lora_mapping,
        N,
        K,
        EM,
        num_tokens,
        num_experts,
        top_k_num,
        lora_ids,
        adapter_enabled,
        lora_a_stacked[0].shape[0],
        qcurr_hidden_states.stride(0),
        qcurr_hidden_states.stride(1),
        w1_lora_a_stacked.stride(0),
        w1_lora_a_stacked.stride(1),
        w1_lora_a_stacked.stride(3),
        w1_lora_a_stacked.stride(2),
        a_intermediate_cache1.stride(2),
        a_intermediate_cache1.stride(3),
        stride_tl,
        stride_el,
        act_scale.stride(0) if act_scale is not None and act_scale.ndim == 2 else 0,
        act_scale.stride(1) if act_scale is not None and act_scale.ndim == 2 else 0,
        w1_lora_a_scale_stacked.stride(0)
        if lora_a_scale_stacked is not None and w1_lora_a_scale_stacked.ndim >= 2
        else 0,
        w1_lora_a_scale_stacked.stride(1)
        if lora_a_scale_stacked is not None and w1_lora_a_scale_stacked.ndim >= 2
        else 0,
        w1_lora_a_scale_stacked.stride(3)
        if lora_a_scale_stacked is not None and w1_lora_a_scale_stacked.ndim == 4
        else 0,
        w1_lora_a_scale_stacked.stride(2)
        if lora_a_scale_stacked is not None and w1_lora_a_scale_stacked.ndim == 4
        else 0,
        0 if block_shape is None else block_shape[0],
        0 if block_shape is None else block_shape[1],
        slice_a_size=qcurr_hidden_states.numel(),
        slice_c_size=a_intermediate_cache1.numel() // num_slices,
        num_slice_a=1,
        num_slice_c=num_slices,
        token_mapping_factor=1 if mul_routed_weight else top_k_num,
        naive_block_assignment=sorted_token_ids is None,
        MUL_ROUTED_WEIGHT=False,
        ADD_INPUTS=False,
        USE_B_L2_CACHE=True,  # new
        IS_PRIMARY=True,
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        per_channel_quant=per_channel_quant,
        **shrink_config,
    )