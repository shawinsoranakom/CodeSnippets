def use_triton_template(
    layout: Layout,
    *,
    enable_int32: bool = False,
    enable_float8: bool = False,
    check_max_autotune: bool = True,
) -> bool:
    from .codegen.common import BackendFeature, has_backend_feature

    layout_dtypes = [torch.float16, torch.bfloat16, torch.float32]
    if enable_int32:
        layout_dtypes = [torch.float16, torch.bfloat16, torch.float32, torch.int32]
    if enable_float8:
        layout_dtypes.extend([torch.float8_e4m3fn, torch.float8_e5m2])
    return (
        (
            (
                is_gpu(layout.device.type)
                and _use_template_for_gpu(layout, layout_dtypes)
            )
            or (layout.device.type == "cpu" and layout.dtype in layout_dtypes)
        )
        # some callers handle max-autotune checking externally
        and (config.max_autotune or config.max_autotune_gemm or not check_max_autotune)
        and _use_autotune_backend("TRITON")
        and has_backend_feature(layout.device, BackendFeature.TRITON_TEMPLATES)
    )