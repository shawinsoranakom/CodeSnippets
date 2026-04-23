def use_nv_universal_gemm_template(
    layout: Layout,
    m: _IntLike,
    n: _IntLike,
    k: _IntLike,
    mat_a: IRNode,
    mat_b: IRNode,
    offs: IRNode | None = None,
    g: _IntLike | None = None,
) -> bool:
    """
    Return True if we can use the NVIDIA Universal GEMM Template.

    Required conditions:
        1. NVGEMM backend is enabled
        2. cutlass_api is available
        3. We are on a NVIDIA GPU
        4. Max autotune or max autotune gemm is enabled
        5. Not in AOT Inductor mode (requires runtime JIT compilation)
        6. Base pointers are 16-byte aligned
        7. Shape dimensions are not unbacked symbols

    Note:
        - Shape and stride constraints are handled internally by
          cutlass_api.get_kernels() which filters incompatible kernels.
        - GroupedGemm currently only supports TN layout (column-major B).
          Any other layout will act as a noop and fall back to ATen.
        - Dynamic shapes are supported as long as they have hints
          (from example inputs).
    """
    from torch.fx.experimental.symbolic_shapes import has_free_unbacked_symbols

    if not ensure_cute_available():
        return False

    if not ensure_nv_universal_gemm_available():
        return False

    if not _use_autotune_backend("NVGEMM"):
        return False

    from .virtualized import V

    if V.aot_compilation:
        return False

    if layout.device.type != "cuda" or torch.version.hip:
        return False

    if not (config.max_autotune or config.max_autotune_gemm):
        return False

    # cutlass_api can't handle unbacked symbols because it needs to evaluate
    # shape constraints (e.g., stride divisibility by 8, N/K divisibility by 16).
    # Unbacked symbols have no hint values, causing GuardOnDataDependentSymNode errors.
    dims_to_check = [m, n, k]
    if g is not None:
        dims_to_check.append(g)
    if any(has_free_unbacked_symbols(dim) for dim in dims_to_check):
        return False

    # Base pointer must be 16-byte aligned. cutlass_api can't check this at
    # compile time because it only sees FakeTensors without real data pointers.
    tensors_to_check = [mat_a, mat_b]
    if offs is not None:
        tensors_to_check.append(offs)
    if any(t.get_name() in V.graph.unaligned_buffers for t in tensors_to_check):
        return False

    return True