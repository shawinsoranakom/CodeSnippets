def convert_to_nvfp4_moe_kernel_format(
    nvfp4_backend: NvFp4MoeBackend,
    layer: torch.nn.Module,
    w13: torch.Tensor,
    w13_scale: torch.Tensor,
    w13_scale_2: torch.Tensor,
    a13_scale: torch.Tensor | None,
    w2: torch.Tensor,
    w2_scale: torch.Tensor,
    w2_scale_2: torch.Tensor,
    a2_scale: torch.Tensor | None,
    is_act_and_mul: bool,
) -> tuple[
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
    torch.Tensor,
]:
    if nvfp4_backend == NvFp4MoeBackend.FLASHINFER_CUTEDSL:
        (
            w13,
            w13_scale,
            w13_scale_2,
            a13_scale,
            w2,
            w2_scale,
            w2_scale_2,
            a2_scale,
        ) = prepare_nvfp4_moe_layer_for_flashinfer_cutedsl(
            layer=layer,
            w13=w13,
            w13_scale=w13_scale,
            w13_scale_2=w13_scale_2,
            a13_scale=a13_scale,
            w2=w2,
            w2_scale=w2_scale,
            w2_scale_2=w2_scale_2,
            a2_scale=a2_scale,
        )
    elif (
        nvfp4_backend in FLASHINFER_NVFP4_MOE_BACKENDS
        or nvfp4_backend == NvFp4MoeBackend.VLLM_CUTLASS
    ):
        (
            w13,
            w13_scale,
            w13_scale_2,
            a13_scale,
            w2,
            w2_scale,
            w2_scale_2,
            a2_scale,
        ) = prepare_nvfp4_moe_layer_for_fi_or_cutlass(
            backend=nvfp4_backend,
            layer=layer,
            w13=w13,
            w13_scale=w13_scale,
            w13_scale_2=w13_scale_2,
            a13_scale=a13_scale,
            w2=w2,
            w2_scale=w2_scale,
            w2_scale_2=w2_scale_2,
            a2_scale=a2_scale,
            is_act_and_mul=is_act_and_mul,
        )
    elif nvfp4_backend == NvFp4MoeBackend.MARLIN:
        a13_scale = None
        a2_scale = None
        (
            w13,
            w13_scale,
            w13_scale_2,
            w2,
            w2_scale,
            w2_scale_2,
        ) = prepare_nvfp4_moe_layer_for_marlin(
            layer=layer,
            w13=w13,
            w13_scale=w13_scale,
            w13_scale_2=w13_scale_2,
            w2=w2,
            w2_scale=w2_scale,
            w2_scale_2=w2_scale_2,
            is_act_and_mul=is_act_and_mul,
        )
    elif nvfp4_backend == NvFp4MoeBackend.EMULATION:
        if a13_scale is None or a2_scale is None:
            raise ValueError(
                "Activation global scales should not be None, got"
                f" a13_scale={a13_scale}, a2_scale={a2_scale}"
            )

        if torch.unique(a13_scale).numel() != 1 or torch.unique(a2_scale).numel() != 1:
            logger.warning_once(
                "In NVFP4 linear, the activation global scale for inputs are different"
                " for MOE w13 (gate_up_proj) layer or MOE w2 (down_proj). Using"
                " a13_scale = a13_scale.max() and a2_scale = a2_scale.max()."
            )

        # 1. We take the max following e.g. quantization/utils/flashinfer_fp4_moe.py.
        # 2. moe_kernel_quantize_input -> ref_nvfp4_quant_dequant
        # use the inverse scale directly (large global scale).
        # NOTE: Before this point, `a13_scale` and `a2_scale` are such that:
        # `FP8_MAX = activation[expert_id].abs().max() * global_scale[expert_id]`,
        # and `global_scale[expert_id]` are small (~1e-4).
        # Taking the largest global scale likely results in overflowing the FP8 range
        # for other experts - other selection strategies may be used.
        a13_scale = 1.0 / a13_scale.max().to(torch.float32)
        a2_scale = 1.0 / a2_scale.max().to(torch.float32)
    else:
        raise ValueError(f"Unknown NvFp4 backend for MoE: {nvfp4_backend}")

    return (
        w13,
        w13_scale,
        w13_scale_2,
        a13_scale,
        w2,
        w2_scale,
        w2_scale_2,
        a2_scale,
    )