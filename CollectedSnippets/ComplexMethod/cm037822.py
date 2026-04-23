def convert_to_fp8_moe_kernel_format(
    fp8_backend: Fp8MoeBackend,
    layer: torch.nn.Module,
    w13: torch.Tensor,
    w2: torch.Tensor,
    w13_scale: torch.Tensor,
    w2_scale: torch.Tensor,
    w13_input_scale: torch.Tensor | None,
    w2_input_scale: torch.Tensor | None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    block_quant = hasattr(layer, "weight_block_size")
    if fp8_backend in [Fp8MoeBackend.DEEPGEMM, Fp8MoeBackend.BATCHED_DEEPGEMM]:
        assert block_quant
        w13, w2, w13_scale, w2_scale = prepare_fp8_moe_layer_for_deepgemm(
            w13,
            w2,
            w13_scale,
            w2_scale,
            tuple(layer.weight_block_size),
        )
    elif fp8_backend == Fp8MoeBackend.AITER:
        w13, w2 = rocm_aiter_ops.shuffle_weights(w13, w2)
    elif fp8_backend == Fp8MoeBackend.MARLIN:
        weight_block_size = getattr(layer, "weight_block_size", None)
        if weight_block_size == [1, 32]:
            from vllm.model_executor.layers.quantization.utils.marlin_utils_fp8 import (
                prepare_mxfp8_moe_layer_for_marlin,
            )

            w13, w2, w13_scale, w2_scale = prepare_mxfp8_moe_layer_for_marlin(
                layer,
                w13,
                w2,
                w13_scale,
                w2_scale,
            )
        else:
            w13, w2, w13_scale, w2_scale = prepare_fp8_moe_layer_for_marlin(
                layer,
                w13,
                w2,
                w13_scale,
                w2_scale,
            )
    elif fp8_backend in [
        Fp8MoeBackend.FLASHINFER_CUTLASS,
        Fp8MoeBackend.FLASHINFER_TRTLLM,
    ]:
        w13, w2, w13_scale, w2_scale = prepare_fp8_moe_layer_for_fi(
            layer=layer,
            w13=w13,
            w2=w2,
            w13_scale=w13_scale,
            w13_input_scale=w13_input_scale,
            w2_scale=w2_scale,
            w2_input_scale=w2_input_scale,
            is_trtllm=(fp8_backend == Fp8MoeBackend.FLASHINFER_TRTLLM),
        )
    elif fp8_backend == Fp8MoeBackend.XPU:
        from vllm.model_executor.layers.fused_moe.xpu_fused_moe import (
            prepare_fp8_moe_layer_for_xpu,
        )

        w13, w2 = prepare_fp8_moe_layer_for_xpu(w13, w2)
    else:
        if fp8_backend not in [
            Fp8MoeBackend.TRITON,
            Fp8MoeBackend.BATCHED_TRITON,
            Fp8MoeBackend.VLLM_CUTLASS,
            Fp8MoeBackend.BATCHED_VLLM_CUTLASS,
            Fp8MoeBackend.XPU,
        ]:
            raise ValueError(f"Unsupported FP8 MoE backend: {fp8_backend.value}")

    return w13, w2, w13_scale, w2_scale