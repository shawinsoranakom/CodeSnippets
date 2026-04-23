def prepare_static_weights_for_trtllm_mxint4_moe(
    gemm1_weights: torch.Tensor,
    gemm1_scales: torch.Tensor,
    gemm2_weights: torch.Tensor,
    gemm2_scales: torch.Tensor,
) -> dict[str, torch.Tensor]:
    """
    Prepare MxInt4 weights for TRT-LLM kernel.

    Input:
        gemm1_weights: [num_experts, 2*intermediate_size, hidden_size//8] int32
            (checkpoint uint4b8 packed) or uint8 (already packed signed int4)
        gemm1_scales: [num_experts, 2*intermediate_size, hidden_size//32] bf16
        gemm2_weights: [num_experts, hidden_size, intermediate_size//8] int32
            (checkpoint uint4b8 packed) or uint8 (already packed signed int4)
        gemm2_scales: [num_experts, hidden_size, intermediate_size//32] bf16

    Returns:
        Dict with keys 'gemm1_weights', 'gemm1_scales', 'gemm2_weights',
            'gemm2_scales' containing shuffled/packed tensors ready for kernel
    """
    from flashinfer import block_scale_interleave
    from flashinfer.fused_moe import (
        convert_to_block_layout,
    )
    from flashinfer.fused_moe.core import (
        _maybe_get_cached_w3_w1_permute_indices,
        get_w2_permute_indices_with_cache,
    )

    from vllm.model_executor.layers.quantization.utils.flashinfer_fp4_moe import (
        reorder_w1w3_to_w3w1,
    )
    from vllm.model_executor.layers.quantization.utils.quant_utils import (
        convert_packed_uint4b8_to_signed_int4_inplace,
    )

    device = gemm1_weights.device
    assert gemm1_weights.ndim == 3, (
        f"Expected a 3D gemm1_weights tensor, got {gemm1_weights.shape}"
    )
    assert gemm1_scales.ndim == 3, (
        f"Expected a 3D gemm1_scales tensor, got {gemm1_scales.shape}"
    )
    assert gemm2_weights.ndim == 3, (
        f"Expected a 3D gemm2_weights tensor, got {gemm2_weights.shape}"
    )
    assert gemm2_scales.ndim == 3, (
        f"Expected a 3D gemm2_scales tensor, got {gemm2_scales.shape}"
    )

    # Convert checkpoint format (uint4b8 in int32) to signed int4
    # Checkpoint stores INT4 as unsigned [0, 15], kernel expects signed [-8, 7]
    if gemm1_weights.dtype == torch.int32 and gemm2_weights.dtype == torch.int32:
        convert_packed_uint4b8_to_signed_int4_inplace(gemm1_weights)
        convert_packed_uint4b8_to_signed_int4_inplace(gemm2_weights)

    gemm1_weights, gemm1_scales = reorder_w1w3_to_w3w1(
        gemm1_weights, gemm1_scales, dim=-2
    )

    _cache_permute_indices: dict[torch.Size, torch.Tensor] = {}
    num_experts = gemm1_weights.shape[0]

    # Convert quantized weights to proper formats -
    gemm1_weights_mxint4 = gemm1_weights.view(torch.uint8)
    assert gemm1_scales.dtype == torch.bfloat16
    gemm2_weights_mxint4 = gemm2_weights.view(torch.uint8)
    assert gemm2_scales.dtype == torch.bfloat16

    epilogue_tile_m = 128
    gemm1_weights_mxint4_shuffled = []
    gemm1_scales_shuffled = []
    gemm2_weights_mxint4_shuffled = []
    gemm2_scales_shuffled = []

    for i in range(num_experts):
        # Calculate the permute indices for the following:
        # 1. Reorder rows of W1 and scales for fused gated activation
        # 2. Shuffle weights and scaling factors for transposed mma output
        # for both w3_w1 and w2 weights and scale factors
        permute_indices = _maybe_get_cached_w3_w1_permute_indices(
            _cache_permute_indices,
            gemm1_weights_mxint4[i],
            epilogue_tile_m,
        )
        gemm1_weights_shuffled = gemm1_weights_mxint4[i][
            permute_indices.to(gemm1_weights.device)
        ].contiguous()
        permute_sf_indices = _maybe_get_cached_w3_w1_permute_indices(
            _cache_permute_indices,
            gemm1_scales[i],
            epilogue_tile_m,
            num_elts_per_sf=32,
        ).to(device)
        gemm1_scales_shuffled.append(
            block_scale_interleave(gemm1_scales[i][permute_sf_indices].contiguous())
        )

        permute_indices = get_w2_permute_indices_with_cache(
            _cache_permute_indices,
            gemm2_weights_mxint4[i],
            epilogue_tile_m,
        )
        gemm2_weights_shuffled = gemm2_weights_mxint4[i][
            permute_indices.to(gemm2_weights.device)
        ].contiguous()

        permute_sf_indices = get_w2_permute_indices_with_cache(
            _cache_permute_indices,
            gemm2_scales[i],
            epilogue_tile_m,
            num_elts_per_sf=16,
        )
        gemm2_scales_shuffled.append(
            block_scale_interleave(
                gemm2_scales[i][permute_sf_indices.to(gemm2_scales.device)].contiguous()
            )
        )

        block_k = 128
        gemm1_weights_shuffled = convert_to_block_layout(
            gemm1_weights_shuffled.view(torch.uint8), block_k
        )
        gemm2_weights_shuffled = convert_to_block_layout(
            gemm2_weights_shuffled.view(torch.uint8), block_k
        )

        gemm1_weights_mxint4_shuffled.append(gemm1_weights_shuffled)
        gemm2_weights_mxint4_shuffled.append(gemm2_weights_shuffled)

    gemm1_weights_mxint4_shuffled = torch.stack(gemm1_weights_mxint4_shuffled)
    gemm2_weights_mxint4_shuffled = torch.stack(gemm2_weights_mxint4_shuffled)
    gemm1_scales_shuffled = torch.stack(gemm1_scales_shuffled).view(torch.bfloat16)
    gemm2_scales_shuffled = torch.stack(gemm2_scales_shuffled).view(torch.bfloat16)
    return {
        "gemm1_weights": gemm1_weights_mxint4_shuffled,
        "gemm1_scales": gemm1_scales_shuffled,
        "gemm2_weights": gemm2_weights_mxint4_shuffled,
        "gemm2_scales": gemm2_scales_shuffled,
    }