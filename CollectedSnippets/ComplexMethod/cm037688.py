def _swizzle_mxfp4(quant_tensor, scale, num_warps=8):
    """weight swizzle for mxfp4 moe, used for OAI mxfp4 kernel"""
    assert has_triton_kernels()
    import triton_kernels.matmul_ogs_details.opt_flags as opt_flags
    from triton_kernels.numerics import InFlexData
    from triton_kernels.tensor import FP4, convert_layout, wrap_torch_tensor
    from triton_kernels.tensor_details import layout
    from triton_kernels.tensor_details.layout import StridedLayout

    value_layout_opts: dict[str, Any] = {}
    scale_layout_opts: dict[str, Any] = {}

    if (
        current_platform.is_cuda()
        and current_platform.is_device_capability(90)
        and not is_torch_equal_or_newer("2.8.1")
    ):
        logger.warning_once(
            "Mxfp4 on hopper is running on torch < 2.8.1, "
            "this cause swizling to be disabled, which may "
            "cause performance degradation. Please upgrade to torch nightly"
        )
        value_layout = StridedLayout
        scale_layout = StridedLayout
    elif current_platform.is_rocm():
        from vllm.platforms.rocm import on_gfx950

        value_layout = StridedLayout
        if on_gfx950():
            try:
                # triton < 3.6
                from triton_kernels.tensor_details.layout import GFX950MXScaleLayout

                scale_layout = GFX950MXScaleLayout
            except ImportError:
                # triton >= 3.6
                from triton_kernels.tensor_details.layout import CDNA4MXScaleLayout

                scale_layout = CDNA4MXScaleLayout
        else:
            scale_layout = StridedLayout
    else:
        value_layout, value_layout_opts = layout.make_default_matmul_mxfp4_w_layout(
            mx_axis=1
        )
        scale_layout, scale_layout_opts = (
            layout.make_default_matmul_mxfp4_w_scale_layout(
                mx_axis=1, num_warps=num_warps
            )
        )
    if current_platform.is_cuda():
        if current_platform.is_device_capability(90):
            constraints = {
                "split_k": 1,
            }
            opt_flags.update_opt_flags_constraints(constraints)
        elif current_platform.is_device_capability_family(100):
            constraints = {
                "is_persistent": True,
                "epilogue_subtile": 1,
            }
            opt_flags.update_opt_flags_constraints(constraints)
    # transpose the tensor so that the quantization axis is on dim1
    quant_tensor = quant_tensor.transpose(-2, -1)
    scale = scale.transpose(-2, -1)
    quant_tensor = convert_layout(
        wrap_torch_tensor(quant_tensor, dtype=FP4), value_layout, **value_layout_opts
    )
    scale = convert_layout(wrap_torch_tensor(scale), scale_layout, **scale_layout_opts)
    return quant_tensor, InFlexData(), scale