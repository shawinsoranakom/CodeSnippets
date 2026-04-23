def _lora_expand_fp8(
    inputs: torch.Tensor,  # shape [num_slices, num_tokens, lora_rank]
    lora_b_weights: list[torch.Tensor],  # FP8 [num_lora, hidden_size, lora_rank]
    output_tensor: torch.Tensor,  # shape [num_tokens, hidden_size * num_slices]
    token_lora_mapping: torch.Tensor,
    token_indices_sorted_by_lora_ids: torch.Tensor,
    num_tokens_per_lora: torch.Tensor,
    lora_token_start_loc: torch.Tensor,
    lora_ids: torch.Tensor,
    no_lora_flag_cpu: torch.Tensor,  # shape [1]
    num_active_loras: int,  # number of active LoRAs (unused here, for API compat)
    b_scale: list[torch.Tensor],  # LoRA B weight scale per slice
    a_scale: torch.Tensor | None = None,  # Scale for shrink output (optional)
    offset_start: int = 0,
    add_inputs: bool = False,
    group_k: int = 0,
    group_n: int = 0,
    use_fp8_w8a8: bool = False,
    per_channel_quant: bool = False,
) -> None:
    """
    FP8-compatible LoRA expand operation.

    Args:
        inputs: Input tensor from shrink operation [num_slices, num_tokens, lora_rank]
        lora_b_weights: List of FP8 LoRA B weights per slice
        output_tensor: Output tensor
        a_scale: Optional scale for input (if input is quantized)
        b_scale: Weight quantization scales per slice
        token_lora_mapping: Token to LoRA ID mapping
        token_indices_sorted_by_lora_ids: Sorted token indices
        num_tokens_per_lora: Number of tokens per LoRA
        lora_token_start_loc: Start location for each LoRA's tokens
        lora_ids: LoRA IDs to process
        no_lora_flag_cpu (torch.Tensor): A CPU tensor of size 1, that indicates
            if there are any requests that require LoRA.
        offset_start (int, optional): Offset start for output_tensor.
            Defaults to 0.
        add_inputs (bool, optional): Whether to add the input tensor to the
            output tensor. Defaults to False.
        group_k (int, optional): Block size for K in block-wise quantization.
        group_n (int, optional): Block size for N in block-wise quantization.
        use_fp8_w8a8 (bool, optional): Whether to use FP8 W8A8 quantization.
        per_channel_quant (bool, optional): Whether to use per-channel quantization.
    """
    assert no_lora_flag_cpu.numel() == 1
    if no_lora_flag_cpu.item():
        # None of the inputs require LoRA.
        return

    if use_fp8_w8a8:
        assert inputs.dtype in [
            torch.float8_e4m3fn,
            torch.float8_e5m2,
        ]
        for weight in lora_b_weights:
            assert weight.dtype in [
                torch.float8_e5m2,
                torch.float8_e4m3fn,
            ]
    else:
        assert inputs.dtype in [torch.float16, torch.bfloat16, torch.float32]
        for weight in lora_b_weights:
            assert weight.dtype in [torch.float16, torch.bfloat16]
    assert inputs.size(0) == len(lora_b_weights)
    assert output_tensor.is_contiguous()

    # metadata sanity check.
    M = inputs.size(1)
    assert token_lora_mapping.size(0) == M
    assert token_lora_mapping.size(0) == token_indices_sorted_by_lora_ids.size(0)
    assert lora_ids.size(0) == num_tokens_per_lora.size(0)
    assert lora_token_start_loc.size(0) == lora_ids.size(0) + 1

    (
        slice_start_tensor,
        lora_ptr_tensor,
        lora_strides_d0_tensor,
        lora_strides_d1_tensor,
        lora_strides_d2_tensor,
        hidden_sizes_tensor,
        same_stride,
        MAX_N,
    ) = _get_lora_b_ptr(lora_b_weights, offset_start, inputs.device)

    # Get scale pointers
    if b_scale is not None:
        b_scale_ptr_tensor = _get_expand_lora_scale_ptr(b_scale, inputs.device)
    else:
        b_scale_ptr_tensor = None
    K = lora_b_weights[0].shape[-1]
    ADD_INPUTS = add_inputs
    MAX_LORAS = lora_ids.size(0)

    CAST_TYPE = False
    NUM_SLICES = len(lora_b_weights)

    # Triton kernel configs.
    kernel_config = get_lora_op_configs(
        op_type="expand",
        max_loras=MAX_LORAS,
        batch=M,
        hidden_size=MAX_N,
        rank=K,
        num_slices=NUM_SLICES,
        add_inputs=add_inputs,
    )
    BLOCK_M = kernel_config["block_m"]
    BLOCK_N = kernel_config["block_n"]
    BLOCK_K = kernel_config["block_k"]
    NUM_WARPS = kernel_config["num_warps"]
    NUM_CTAS = kernel_config.get("num_ctas", 1)
    NUM_STAGES = kernel_config["num_stages"]

    EVEN_K = K % BLOCK_K == 0

    grid = (
        triton.cdiv(M, BLOCK_M) * triton.cdiv(MAX_N, BLOCK_N),
        NUM_SLICES,
        num_active_loras,
    )
    # We disable PDL temporarily because LoRA kernels are not launching back-to-back,
    # making PDL invalid and affecting the kernel performance.
    use_gdc = False  # supports_pdl(inputs.device)
    # Get scale strides
    if a_scale is not None:
        a_scale_m_stride = a_scale.stride(0) if a_scale.dim() > 1 else 0
        a_scale_k_stride = a_scale.stride(-1) if a_scale.dim() > 1 else 0
    else:
        a_scale_m_stride = 0
        a_scale_k_stride = 0

    if b_scale is not None and b_scale[0].dim() > 0:
        b_scale_l_stride = b_scale[0].stride(0) if b_scale[0].dim() > 0 else 0
        b_scale_n_stride = (
            b_scale[0].stride(-2)
            if b_scale[0].dim() > 2
            else (b_scale[0].stride(-1) if b_scale[0].dim() > 1 else 1)
        )
        b_scale_k_stride = b_scale[0].stride(-1) if b_scale[0].dim() > 2 else 0
    else:
        b_scale_l_stride = 1
        b_scale_n_stride = 0
        b_scale_k_stride = 0

    _lora_expand_kernel_fp8[grid](
        inputs,
        lora_ptr_tensor,
        output_tensor,
        a_scale,
        b_scale_ptr_tensor,
        M,
        MAX_N,
        K,
        token_indices_sorted_by_lora_ids,
        num_tokens_per_lora,
        lora_token_start_loc,
        lora_ids,
        slice_start_tensor,
        inputs.stride(0),
        inputs.stride(1),
        inputs.stride(2),
        lora_strides_d0_tensor,
        lora_strides_d1_tensor,
        lora_strides_d2_tensor,
        a_scale_m_stride,
        a_scale_k_stride,
        b_scale_l_stride,
        b_scale_n_stride,
        b_scale_k_stride,
        output_tensor.stride(0),
        output_tensor.stride(1),
        hidden_sizes_tensor,
        group_n,
        group_k,
        BLOCK_M,
        BLOCK_N,
        BLOCK_K,
        EVEN_K,
        ADD_INPUTS,
        CAST_TYPE,
        NUM_SLICES,
        same_stride,
        use_gdc,
        use_fp8_w8a8=use_fp8_w8a8,
        per_channel_quant=per_channel_quant,
        num_warps=NUM_WARPS,
        num_ctas=NUM_CTAS,
        num_stages=NUM_STAGES,
        launch_pdl=use_gdc,
    )

    return