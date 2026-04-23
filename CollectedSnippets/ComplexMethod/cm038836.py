def _lora_shrink_fp8(
    inputs: torch.Tensor,  # shape [num_tokens, hidden_size] - FP8 or FP16/BF16
    lora_a_weights: list[
        torch.Tensor
    ],  # shape [num_loras, lora_rank, hidden_size] - FP8 or FP16/BF16
    output_tensor: torch.Tensor,  # shape [num_slices, num_tokens, lora_rank]
    token_lora_mapping: torch.Tensor,  # shape [num_tokens]
    token_indices_sorted_by_lora_ids: torch.Tensor,  # shape [num_tokens]
    num_tokens_per_lora: torch.Tensor,  # shape [max-loras + 1]
    lora_token_start_loc: torch.Tensor,  # shape [max-loras + 2]
    lora_ids: torch.Tensor,  # shape [max-loras + 1]
    no_lora_flag_cpu: torch.Tensor,  # shape [1]
    num_active_loras: int,  # number of active LoRAs (unused here, for API compat)
    scaling: float,
    b_scale: list[torch.Tensor],  # LoRA weight scale per slice
    a_scale: torch.Tensor | None = None,  # Activation scale - per-token or block-wise
    group_k: int = 0,  # Block size for K in block-wise quantization (0 = tensor-wise)
    group_n: int = 0,  # Block size for N in block-wise quantization
    use_fp8_w8a8: bool = False,
    per_channel_quant: bool = False,
) -> None:
    """
    Args:
        inputs: FP8 or FP16/BF16 input tensor [num_tokens, hidden_size]
        lora_a_weights: List of FP8 or FP16/BF16 LoRA A weights per slice
        output_tensor: Output tensor (FP16/BF16/FP32)
        token_lora_mapping: Token to LoRA ID mapping
        token_indices_sorted_by_lora_ids: Sorted token indices
        num_tokens_per_lora: Number of tokens per LoRA
        lora_token_start_loc: Start location for each LoRA's tokens
        lora_ids: LoRA IDs to process
        scaling: LoRA scaling factor
        a_scale: Activation quantization scales
        b_scale: Weight quantization scales per slice
        group_k: Block size for K dimension quantization
        group_n: Block size for N dimension quantization
        use_fp8_w8a8: Whether to use FP8 weights and activations
        per_channel_quant: Whether to use per-channel quantization
    """
    assert no_lora_flag_cpu.numel() == 1
    if no_lora_flag_cpu.item():
        # None of the inputs require LoRA.
        return

    assert inputs.size(1) == lora_a_weights[0].size(-1)
    assert inputs.is_contiguous()
    assert output_tensor.is_contiguous()

    # metadata sanity check
    M = inputs.size(0)
    assert token_lora_mapping.size(0) == M
    assert token_lora_mapping.size(0) == token_indices_sorted_by_lora_ids.size(0)
    assert lora_ids.size(0) == num_tokens_per_lora.size(0)
    assert lora_token_start_loc.size(0) == lora_ids.size(0) + 1

    output_tensor.zero_()

    # Get LoRA weight pointers
    (lora_ptr_tensor, lora_strides_d0, lora_strides_d1, lora_strides_d2) = (
        _get_lora_a_ptr(lora_a_weights, inputs.device)
    )

    # Get scale pointers if using FP8
    if use_fp8_w8a8:
        assert a_scale is not None, "a_scale required for FP8 w8a8"
        assert b_scale is not None, "b_scale required for FP8"

        b_scale_ptr_tensor, b_scale_l_stride, b_scale_n_stride, b_scale_k_stride = (
            _get_shrink_lora_scale_ptr(b_scale, inputs.device)
        )
        a_scale_ptr = (
            a_scale if a_scale is not None else torch.tensor(1.0, device=inputs.device)
        )
    else:
        b_scale_ptr_tensor = torch.tensor(0, device=inputs.device)
        b_scale_l_stride = 0
        b_scale_n_stride = 0
        b_scale_k_stride = 0
        a_scale_ptr = torch.tensor(0, device=inputs.device)

    N, K = lora_a_weights[0].shape[-2:]  # K=hidden_size, N=rank
    NUM_SLICES = len(lora_a_weights)
    MAX_LORAS = lora_ids.size(0)

    # Triton kernel configs
    kernel_config = get_lora_op_configs(
        "shrink",
        max_loras=MAX_LORAS,
        batch=M,
        hidden_size=K,
        rank=N,
        num_slices=NUM_SLICES,
    )
    BLOCK_M = kernel_config["block_m"]
    BLOCK_N = kernel_config["block_n"]
    BLOCK_K = kernel_config["block_k"]
    SPLIT_K = kernel_config["split_k"]
    NUM_WARPS = kernel_config["num_warps"]
    NUM_STAGES = kernel_config["num_stages"]
    NUM_CTAS = kernel_config["num_ctas"]
    GROUP_SIZE_M = kernel_config.get("group_size_m", 8)
    assert BLOCK_K is not None and SPLIT_K is not None
    EVEN_K = K % (BLOCK_K * SPLIT_K) == 0

    # Grid configuration with column-major ordering support
    grid = (
        SPLIT_K * triton.cdiv(M, BLOCK_M) * triton.cdiv(N, BLOCK_N),
        NUM_SLICES,
        num_active_loras,
    )

    # Determine scale strides
    if use_fp8_w8a8:
        if a_scale is not None and a_scale.ndim == 2:
            a_scale_m_stride = a_scale.stride(0)
            a_scale_k_stride = a_scale.stride(1)
        else:
            a_scale_m_stride = 0
            a_scale_k_stride = 0
    else:
        a_scale_m_stride = 0
        a_scale_k_stride = 0

    # We disable PDL temporarily because LoRA kernels are not launching back-to-back,
    # making PDL invalid and affecting the kernel performance.
    use_gdc = False  # supports_pdl(inputs.device)
    _lora_shrink_kernel_fp8[grid](
        inputs,
        lora_ptr_tensor,
        output_tensor,
        a_scale_ptr,
        b_scale_ptr_tensor,
        M,
        N,
        K,
        token_indices_sorted_by_lora_ids,
        num_tokens_per_lora,
        lora_token_start_loc,
        lora_ids,
        scaling,
        inputs.stride(0),
        inputs.stride(1),
        lora_strides_d0,
        lora_strides_d1,
        lora_strides_d2,
        a_scale_m_stride,
        a_scale_k_stride,
        b_scale_l_stride,
        b_scale_n_stride,
        b_scale_k_stride,
        output_tensor.stride(0),
        output_tensor.stride(1),
        output_tensor.stride(2),
        group_n,
        group_k,
        BLOCK_M,
        BLOCK_N,
        BLOCK_K,
        EVEN_K,
        SPLIT_K,
        GROUP_SIZE_M,
        NUM_SLICES,
        use_gdc,
        use_fp8_w8a8,
        per_channel_quant,
        use_gdc,
        num_warps=NUM_WARPS,
        num_ctas=NUM_CTAS,
        num_stages=NUM_STAGES,
    )

    return