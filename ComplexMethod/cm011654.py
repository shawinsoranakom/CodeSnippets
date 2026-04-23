def use_blackwell_cutedsl_grouped_mm(
    mat_a: Any,
    mat_b: Any,
    layout: Layout,
    a_is_2d: bool,
    b_is_2d: bool,
    offs: Any | None,
    bias: Any | None,
    scale_result: Any | None,
) -> bool:
    """
    Returns True if we can use the blackwell kernel for grouped mm.
    Required conditions:
        1. CuTeDSL backend is enabled
        2. CuTeDSL is available
        3. We are on a blackwell arch
        4. The dtype is bf16
        5. Max autotune or max autotune gemm is enabled
        6. A, B, and the output are 16B aligned
        7. We are not using dynamic shapes
        8. A is 2d
        9. B is 3d
        10. Offsets are provided
        11. Bias and Scale are not provided
    """
    if not ensure_cute_available():
        return False

    if not _use_autotune_backend("CUTEDSL"):
        return False

    from .codegen.cuda.cuda_env import is_datacenter_blackwell_arch

    if not is_gpu(layout.device.type):
        return False

    if not is_datacenter_blackwell_arch():
        return False

    layout_dtypes = [torch.bfloat16]
    if not _use_template_for_gpu(layout, layout_dtypes):
        return False

    if not (config.max_autotune or config.max_autotune_gemm):
        return False

    # Checks for 16B ptr and stride alignment
    if not can_use_tma(mat_a, mat_b, output_layout=layout):
        return False

    if any(is_dynamic(x) for x in [mat_a, mat_b]):
        return False

    if not a_is_2d or b_is_2d:
        return False

    if offs is None:
        return False

    if bias is not None or scale_result is not None:
        return False

    return True