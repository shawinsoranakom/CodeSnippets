def _fused_moe_lora_expand_fp8(
    output: torch.Tensor,  # (num_tokens, top_k_num, N*len(lora_a_stacked),)
    a_intermediate_cache1: torch.Tensor,  # (num_slices, M, top_k_num, max_lora_rank)
    lora_b_stacked: list[
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
    max_lora_rank: int,
    w1_output_dim_size: int,
    block_size_m: int,
    block_size_n: int,
    block_size_k: int,
    group_size_m: int,
    num_warps: int,
    num_stages: int,
    split_k: int,
    num_active_loras: int,
    lora_b_scale_stacked: list[torch.Tensor],
    mul_routed_weight: bool = False,
    offset: int = 0,
    use_gdc: bool = False,
    act_scale: torch.Tensor | None = None,
    use_fp8_w8a8: bool = False,
    use_int8_w8a8: bool = False,
    use_int8_w8a16: bool = False,
    per_channel_quant: bool = False,
    block_shape: List[int] | None = None,  # noqa: UP006, UP007
) -> None:
    if use_fp8_w8a8 or use_int8_w8a8:
        assert lora_b_scale_stacked is not None, (
            "lora_b_scale_stacked must be provided for w8a8 quantization"
        )
        assert block_shape is None or triton.cdiv(
            lora_b_stacked[0].size(-2), block_shape[0]
        ) == lora_b_scale_stacked[0].size(-2), (
            "Incompatible block shape for lora_b_scale_stacked.size(-2) "
        )
        assert block_shape is None or triton.cdiv(
            lora_b_stacked[0].size(-1), block_shape[1]
        ) == lora_b_scale_stacked[0].size(-1), (
            "Incompatible block shape for lora_b_scale_stacked.size(-1) "
        )
    elif use_int8_w8a16:
        assert lora_b_scale_stacked is not None, (
            "lora_b_scale_stacked must be provided for w8a16 quantization"
        )
        assert block_shape is None or block_shape[0] == 0, (
            "Block shape for activation must be 0 for w8a16"
        )
    else:
        assert act_scale is None
        assert lora_b_scale_stacked is None

    if lora_b_scale_stacked is not None:
        b_scale_ptr = _get_ptr(lora_b_scale_stacked, device)
        w1_lora_b_scale_stacked = lora_b_scale_stacked[0]

    if block_shape is not None:
        block_size_k = min(block_size_k, min(block_shape[0], block_shape[1]))

    b_ptr = _get_ptr(lora_b_stacked, device)
    K = max_lora_rank
    N = w1_output_dim_size

    w1_lora_b_stacked = lora_b_stacked[0]

    a_intermediate_cache1 = a_intermediate_cache1.view(
        -1, a_intermediate_cache1.shape[3]
    )

    expand_config = {
        "BLOCK_SIZE_M": block_size_m,
        "BLOCK_SIZE_N": block_size_n,
        "BLOCK_SIZE_K": block_size_k,
        "GROUP_SIZE_M": group_size_m,
        "num_warps": num_warps,
        "num_stages": num_stages,
        "SPLIT_K": 1,  # Set split_k = 1 for expand calls
        "USE_GDC": use_gdc,
        "launch_pdl": use_gdc,  # triton kernel metadata
    }

    grid_lora_dim, stride_tl, stride_el = _adjust_kernel_inputs(
        num_active_loras, sorted_token_ids, expert_ids
    )

    grid = lambda META: (
        triton.cdiv(EM, META["BLOCK_SIZE_M"]) * triton.cdiv(N, META["BLOCK_SIZE_N"]),
        len(lora_b_stacked),
        grid_lora_dim,
    )

    # Fast path: directly accumulate into the corresponding slice interval of output.
    out_view = output[:, :, offset : offset + num_slices * N]
    slice_c_size = N * out_view.stride(2)

    _fused_moe_lora_kernel_fp8[grid](
        a_intermediate_cache1,
        b_ptr,
        out_view,
        act_scale,
        b_scale_ptr if lora_b_scale_stacked is not None else None,
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
        lora_b_stacked[0].shape[0],
        a_intermediate_cache1.stride(0),
        a_intermediate_cache1.stride(1),
        w1_lora_b_stacked.stride(0),
        w1_lora_b_stacked.stride(1),
        w1_lora_b_stacked.stride(3),
        w1_lora_b_stacked.stride(2),
        out_view.stride(1),
        out_view.stride(2),
        stride_tl,
        stride_el,
        act_scale.stride(0) if act_scale is not None and act_scale.ndim == 2 else 0,
        act_scale.stride(1) if act_scale is not None and act_scale.ndim == 2 else 0,
        w1_lora_b_scale_stacked.stride(0)
        if lora_b_scale_stacked is not None and w1_lora_b_scale_stacked.ndim >= 2
        else 0,
        w1_lora_b_scale_stacked.stride(1)
        if lora_b_scale_stacked is not None and w1_lora_b_scale_stacked.ndim >= 2
        else 0,
        w1_lora_b_scale_stacked.stride(3)
        if lora_b_scale_stacked is not None and w1_lora_b_scale_stacked.ndim == 4
        else 0,
        w1_lora_b_scale_stacked.stride(2)
        if lora_b_scale_stacked is not None and w1_lora_b_scale_stacked.ndim == 4
        else 0,
        0 if block_shape is None else block_shape[0],
        0 if block_shape is None else block_shape[1],
        slice_a_size=a_intermediate_cache1.numel() // num_slices,
        slice_c_size=slice_c_size,
        num_slice_a=num_slices,
        num_slice_c=num_slices,
        token_mapping_factor=1,
        naive_block_assignment=sorted_token_ids is None,
        MUL_ROUTED_WEIGHT=mul_routed_weight,
        ADD_INPUTS=True,
        USE_B_L2_CACHE=True,  # new
        IS_PRIMARY=False,
        use_fp8_w8a8=use_fp8_w8a8,
        use_int8_w8a8=use_int8_w8a8,
        use_int8_w8a16=use_int8_w8a16,
        per_channel_quant=per_channel_quant,
        **expand_config,
    )