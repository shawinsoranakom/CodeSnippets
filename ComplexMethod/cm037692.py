def prepare_fp8_moe_layer_for_fi(
    layer: torch.nn.Module,
    w13: torch.Tensor,
    w2: torch.Tensor,
    w13_scale: torch.Tensor,
    w13_input_scale: torch.Tensor | None,
    w2_scale: torch.Tensor,
    w2_input_scale: torch.Tensor | None,
    is_trtllm: bool = False,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Convert Fp8 MoE weights to flashinfer kernel format

    Note that for trtllm we update the model state dict
    with the scale format needed for these kernels.

    Note that for per-tensor, we update the layer's
    intermediate size if the weights needed padding.
    """

    assert hasattr(layer.moe_config, "is_act_and_mul")
    block_quant = (
        hasattr(layer, "weight_block_size") and layer.weight_block_size is not None
    )
    is_mxfp8 = block_quant and w13_scale.dtype == torch.uint8
    is_deepseek_fp8 = block_quant and not is_mxfp8
    is_gated = layer.activation.is_gated

    # MXFP8 TRT-LLM requires W31 swap + reorder + shuffle.
    if is_mxfp8 and is_trtllm:
        # FlashInfer TRT-LLM SwiGLU expects [up; gate] but vLLM stores
        # [gate; up].  Swap both weights and scales before interleaving.
        if layer.moe_config.is_act_and_mul:
            w13 = swap_w13_to_w31(w13)
            # Scales may be 2D [E, flat] from _quantize_mxfp8_moe_weight;
            # reshape to 3D so swap_w13_to_w31 can flip the two halves,
            # then flatten back.
            if w13_scale.ndim == 2:
                num_rows = w13.shape[1]  # 2 * intermediate_size
                w13_scale = w13_scale.reshape(w13_scale.shape[0], num_rows, -1)
                w13_scale = swap_w13_to_w31(w13_scale)
                w13_scale = w13_scale.reshape(w13_scale.shape[0], -1)
            else:
                w13_scale = swap_w13_to_w31(w13_scale)

        w13, w2, w13_scale, w2_scale = _shuffle_mxfp8_moe_weights(
            w13, w2, w13_scale, w2_scale, is_gated
        )
        return w13, w2, w13_scale, w2_scale

    # Some FI MoE kernels require internal alignment of 16
    # for the gate-up proj. Pad the weights to respect this.
    if not block_quant:
        min_alignment = 16 if is_gated else 128
        w13, w2, new_intermediate = align_fp8_moe_weights_for_fi(
            w13,
            w2,
            layer.moe_config.is_act_and_mul,
            min_alignment,
        )
        layer.moe_config.intermediate_size_per_partition = new_intermediate

    # FI kernels require W31 layout rather than W13.
    if layer.moe_config.is_act_and_mul:
        w13 = swap_w13_to_w31(w13)
        if block_quant:
            w13_scale = swap_w13_to_w31(w13_scale)

    # DeepSeekFp8 TRT-LLM: shuffle weights into BlockMajorK layout.
    if is_deepseek_fp8 and is_trtllm:
        w13, w2 = _shuffle_deepseek_fp8_moe_weights(w13, w2)

    # FI TRT-LLM FP8 per-tensor MoE kernel requires weight shuffle
    # and registration of alpha scales.
    if is_trtllm and not block_quant:
        assert w13_input_scale is not None
        assert w2_input_scale is not None

        rotate_weights_for_fi_trtllm_fp8_per_tensor_moe(w13, w2, is_gated)

    # Clamp block scales to avoid NaN from the FlashInfer CUTLASS kernel.
    # Some FP8 models have near-zero block scales (~1e-23) for dead/unused
    # experts. The CUTLASS kernel doesn't handle these correctly on Hopper
    # (SM 9.0), producing NaN instead of near-zero output. Clamping to a
    # small minimum prevents this without affecting model accuracy since
    # these experts' effective weights are already zero.
    if block_quant:
        _FI_CUTLASS_MIN_BLOCK_SCALE = 1e-10
        w13_scale.clamp_(min=_FI_CUTLASS_MIN_BLOCK_SCALE)
        w2_scale.clamp_(min=_FI_CUTLASS_MIN_BLOCK_SCALE)

    return w13, w2, w13_scale, w2_scale