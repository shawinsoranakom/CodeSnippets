def convert_gpt_oss_weight_to_mxfp4_moe_kernel_format(
    mxfp4_backend: Mxfp4MoeBackend,
    layer: torch.nn.Module,
    w13_weight: torch.Tensor,
    w2_weight: torch.Tensor,
    w13_weight_scale: torch.Tensor,
    w2_weight_scale: torch.Tensor,
    w13_bias: torch.Tensor | None = None,
    w2_bias: torch.Tensor | None = None,
    _cache_permute_indices: dict[torch.Size, torch.Tensor] | None = None,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    Union[torch.Tensor, "PrecisionConfig"],
    Union[torch.Tensor, "PrecisionConfig"],
    torch.Tensor | None,
    torch.Tensor | None,
]:
    """Convert loaded weights into backend-specific kernel format."""

    num_experts = w13_weight.shape[0]
    intermediate_size = w13_weight.shape[1] // 2
    hidden_size = w13_weight.shape[2] * 2

    sf_block_size = 32  # mxfp4 block size

    if mxfp4_backend in (
        Mxfp4MoeBackend.MARLIN,
        Mxfp4MoeBackend.BATCHED_MARLIN,
    ):
        from vllm.model_executor.layers.quantization.utils.marlin_utils_fp4 import (
            prepare_moe_mxfp4_layer_for_marlin,
        )

        return prepare_moe_mxfp4_layer_for_marlin(
            layer,
            w13_weight,
            w2_weight,
            w13_weight_scale,
            w2_weight_scale,
            w13_bias,
            w2_bias,
        )

    elif mxfp4_backend in TRTLLM_BACKENDS:
        assert _cache_permute_indices is not None
        from flashinfer.fp4_quantization import nvfp4_block_scale_interleave
        from flashinfer.fused_moe.core import get_w2_permute_indices_with_cache

        # gemm1_alpha/beta/clamp_limit are created by the expert class
        # (TrtLlmMxfp4ExpertsBase), not on the layer.

        w13_weight = w13_weight.data
        w2_weight = w2_weight.data
        w13_weight_scale = w13_weight_scale.data
        w2_weight_scale = w2_weight_scale.data
        assert w13_bias is not None and w2_bias is not None
        w13_bias = w13_bias.data.to(torch.float32)
        w2_bias = w2_bias.data.to(torch.float32)

        # Swap w1 and w3 as the definition of swiglu is different in trtllm-gen
        def swap_every_two_rows(x, axis=-1):
            shape = x.shape
            if axis < 0:
                axis = len(shape) + axis
            new_shape = list(shape)
            new_shape[axis] = shape[axis] // 2
            new_shape.insert(axis + 1, 2)
            x = x.reshape(*new_shape)
            x = x.flip(axis + 1)
            new_shape = list(shape)
            return x.reshape(*new_shape)

        w13_weight_scale = swap_every_two_rows(w13_weight_scale, -2)
        w13_weight = swap_every_two_rows(w13_weight, -2)
        w13_bias = swap_every_two_rows(w13_bias, -1)

        # Shuffle weights and scaling factors for transposed mma output
        gemm1_weights_shuffled = []
        gemm1_scales_shuffled = []
        gemm2_weights_shuffled = []
        gemm2_scales_shuffled = []
        gemm1_bias_shuffled = []
        gemm2_bias_shuffled = []
        epilogue_tile_m = 128
        for i in range(num_experts):
            # w13 weight
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_weight[i].view(torch.uint8),
                epilogue_tile_m,
            )
            gemm1_weights_shuffled.append(
                w13_weight[i]
                .view(torch.uint8)[permute_indices.to(w13_weight.device)]
                .contiguous()
            )
            # w13 scale
            permute_sf_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_weight_scale[i].view(torch.uint8),
                epilogue_tile_m,
                num_elts_per_sf=16,
            )
            gemm1_scales_shuffled.append(
                nvfp4_block_scale_interleave(
                    w13_weight_scale[i]
                    .view(torch.uint8)[permute_sf_indices.to(w13_weight_scale.device)]
                    .contiguous()
                )
            )
            # w13 bias
            permute_bias_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w13_bias[i].clone().reshape(-1, 1),
                epilogue_tile_m,
            )
            gemm1_bias_shuffled.append(
                w13_bias[i]
                .clone()
                .reshape(-1, 1)[permute_bias_indices.to(w13_bias.device)]
                .contiguous()
            )
            # w2 weight
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_weight[i].view(torch.uint8),
                epilogue_tile_m,
            )
            gemm2_weights_shuffled.append(
                w2_weight[i]
                .view(torch.uint8)[permute_indices.to(w2_weight.device)]
                .contiguous()
            )
            # w2 scale
            permute_sf_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_weight_scale[i].view(torch.uint8),
                epilogue_tile_m,
                num_elts_per_sf=16,
            )
            gemm2_scales_shuffled.append(
                nvfp4_block_scale_interleave(
                    w2_weight_scale[i]
                    .view(torch.uint8)[permute_sf_indices.to(w2_weight_scale.device)]
                    .contiguous()
                )
            )
            # w2 bias
            permute_indices = get_w2_permute_indices_with_cache(
                _cache_permute_indices,
                w2_bias[i].clone().reshape(-1, 1),
                epilogue_tile_m,
            )
            gemm2_bias_shuffled.append(
                w2_bias[i]
                .clone()
                .reshape(-1, 1)[permute_indices.to(w2_bias.device)]
                .contiguous()
            )

        w13_weight = torch.stack(gemm1_weights_shuffled)
        w13_weight_scale = (
            torch.stack(gemm1_scales_shuffled)
            .reshape(num_experts, 2 * intermediate_size, hidden_size // sf_block_size)
            .view(torch.float8_e4m3fn)
        )
        w2_weight = torch.stack(gemm2_weights_shuffled)
        w2_weight_scale = (
            torch.stack(gemm2_scales_shuffled)
            .reshape(num_experts, hidden_size, intermediate_size // sf_block_size)
            .view(torch.float8_e4m3fn)
        )
        w13_bias = torch.stack(gemm1_bias_shuffled).reshape(num_experts, -1)
        w2_bias = torch.stack(gemm2_bias_shuffled).reshape(num_experts, -1)

        return (
            w13_weight,
            w2_weight,
            w13_weight_scale,
            w2_weight_scale,
            w13_bias,
            w2_bias,
        )

    elif mxfp4_backend in (
        Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_BF16,
        Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_MXFP8,
    ):
        # De-interleave and swap for w13 weight, bias, and scales
        w13_w = w13_weight.data
        gate_w, up_w = w13_w[:, ::2, :], w13_w[:, 1::2, :]
        deinterleaved_w13_w = torch.cat([gate_w, up_w], dim=1)
        w1_w, w3_w = torch.chunk(deinterleaved_w13_w, 2, dim=1)
        w13_weight_swapped = torch.cat([w3_w, w1_w], dim=1)

        assert w13_bias is not None and w2_bias is not None
        w13_b = w13_bias.data.to(torch.float32)
        gate_b, up_b = w13_b[:, ::2], w13_b[:, 1::2]
        deinterleaved_w13_b = torch.cat([gate_b, up_b], dim=1)
        b1, b3 = torch.chunk(deinterleaved_w13_b, 2, dim=-1)
        w13_bias_swapped = torch.cat([b3, b1], dim=-1).to(torch.bfloat16)

        w13_s = w13_weight_scale.data
        gate_s, up_s = w13_s[:, ::2, :], w13_s[:, 1::2, :]
        deinterleaved_w13_s = torch.cat([gate_s, up_s], dim=1)
        s1, s3 = torch.chunk(deinterleaved_w13_s, 2, dim=1)
        w13_scale_swapped = torch.cat([s3, s1], dim=1)

        if mxfp4_backend == Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_MXFP8:
            from flashinfer import block_scale_interleave

            orig_shape = w13_scale_swapped.shape
            w13_scale_interleaved = block_scale_interleave(
                w13_scale_swapped.view(torch.uint8)
            ).reshape(orig_shape)

            w2_s = w2_weight_scale.data
            orig_shape = w2_s.shape
            w2_scale_interleaved = block_scale_interleave(
                w2_s.view(torch.uint8)
            ).reshape(orig_shape)

            return (
                w13_weight_swapped,
                w2_weight,
                w13_scale_interleaved,
                w2_scale_interleaved,
                w13_bias_swapped,
                w2_bias,
            )

        else:
            assert mxfp4_backend == Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_BF16

            def _interleave_mxfp4_cutlass_sm90(w):
                w_shape = w.shape
                w_interleaved = w.reshape(w_shape[0], w_shape[1], (w_shape[2] // 4), 4)
                w_interleaved = w_interleaved.permute(0, 2, 1, 3)
                w_interleaved = w_interleaved.reshape(
                    w_shape[0], w_shape[2] // 4, w_shape[1] * 4
                )
                return w_interleaved

            w31_scales = w13_scale_swapped.to(torch.uint8)
            w31_scales_interleaved = _interleave_mxfp4_cutlass_sm90(w31_scales)

            w2_scale = w2_weight_scale.data.to(torch.uint8)
            w2_scale_interleaved = _interleave_mxfp4_cutlass_sm90(w2_scale)

            return (
                w13_weight_swapped,
                w2_weight,
                w31_scales_interleaved,
                w2_scale_interleaved,
                w13_bias_swapped,
                w2_bias,
            )

    elif mxfp4_backend == Mxfp4MoeBackend.AITER:
        from vllm._aiter_ops import rocm_aiter_ops

        if w13_bias is not None:
            w13_bias = w13_bias.data.to(torch.float32)
        if w2_bias is not None:
            w2_bias = w2_bias.data.to(torch.float32)

        e, n, k = w13_weight.shape

        # De-interleave w13 rows: gate/up pairs -> contiguous gate, up blocks
        w13_weight.view(torch.uint8).copy_(
            w13_weight.data.view(torch.uint8)
            .view(e, n // 2, 2, k)
            .permute(0, 2, 1, 3)
            .contiguous()
            .view(e, n, k)
        )
        w13_weight_scale.data = (
            w13_weight_scale.data.view(e, n // 2, 2, -1)
            .permute(0, 2, 1, 3)
            .contiguous()
            .view(e, n, -1)
        )

        # View as native FP4 dtype for AITER shuffle
        w13_weight.data = w13_weight.data.view(torch.float4_e2m1fn_x2)
        w2_weight.data = w2_weight.data.view(torch.float4_e2m1fn_x2)

        # Shuffle weights and scales for AITER CK kernel layout
        w13_weight.data = rocm_aiter_ops.shuffle_weight_a16w4(w13_weight, 16, True)
        shuffled_w13_scale = rocm_aiter_ops.shuffle_scale_a16w4(
            w13_weight_scale.view(-1, w13_weight_scale.shape[-1]),
            num_experts,
            True,
        )

        w2_weight.data = rocm_aiter_ops.shuffle_weight_a16w4(w2_weight, 16, False)
        shuffled_w2_scale = rocm_aiter_ops.shuffle_scale_a16w4(
            w2_weight_scale.view(-1, w2_weight_scale.shape[-1]),
            num_experts,
            False,
        )

        # Permute bias to match de-interleaved weight layout
        if w13_bias is not None:
            w13_bias = (
                w13_bias.data.view(-1, n // 2, 2)
                .permute(0, 2, 1)
                .contiguous()
                .view(-1, n)
            )

        return (
            w13_weight,
            w2_weight,
            shuffled_w13_scale,
            shuffled_w2_scale,
            w13_bias,
            w2_bias,
        )

    elif mxfp4_backend in TRITON_BACKENDS:
        from triton_kernels.matmul_ogs import FlexCtx, PrecisionConfig

        assert w13_bias is not None and w2_bias is not None
        w13_bias = w13_bias.to(torch.float32)
        w2_bias = w2_bias.to(torch.float32)

        w13_weight, w13_flex, w13_scale = _swizzle_mxfp4(
            w13_weight,
            w13_weight_scale,
        )
        w2_weight, w2_flex, w2_scale = _swizzle_mxfp4(
            w2_weight,
            w2_weight_scale,
        )

        w13_precision_config = PrecisionConfig(
            weight_scale=w13_scale, flex_ctx=FlexCtx(rhs_data=w13_flex)
        )
        w2_precision_config = PrecisionConfig(
            weight_scale=w2_scale, flex_ctx=FlexCtx(rhs_data=w2_flex)
        )

        del layer.w13_weight
        del layer.w2_weight

        return (
            w13_weight,
            w2_weight,
            w13_precision_config,
            w2_precision_config,
            w13_bias,
            w2_bias,
        )
    elif mxfp4_backend == Mxfp4MoeBackend.XPU:
        # No additional transformation needed for XPU backend
        return (
            w13_weight,
            w2_weight,
            w13_weight_scale,
            w2_weight_scale,
            w13_bias,
            w2_bias,
        )
    elif mxfp4_backend == Mxfp4MoeBackend.EMULATION:
        # No additional transformation needed for emulation backend,
        # weights are dequantized on the fly in the experts class.
        return (
            w13_weight,
            w2_weight,
            w13_weight_scale,
            w2_weight_scale,
            w13_bias,
            w2_bias,
        )
    else:
        raise ValueError(
            f"Unsupported mxfp4_backend: {mxfp4_backend}: "
            f"should be one of: {list(Mxfp4MoeBackend)}."
        )