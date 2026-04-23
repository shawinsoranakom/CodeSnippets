def _load_deepgemm_kernel():
    """Lazily load the DeepGEMM kernel and extract functions with proper names.

    Uses the hub kernels lazy loading pattern. Raises an error if the kernel
    cannot be loaded, required functions are missing, or the hardware is insufficient.
    Only attempts loading once.
    """
    global _deepgemm_available, deepgemm_fp8_matmul, deepgemm_grouped_fp8_matmul, deepgemm_per_token_cast_to_fp8

    if _deepgemm_available is not None:
        if not _deepgemm_available:
            raise ImportError("DeepGEMM kernel is not available (previous load attempt failed).")
        return

    _deepgemm_available = False  # mark attempted before any early exit

    # DeepGEMM requires CUDA and a compatible GPU
    if not torch.cuda.is_available():
        raise ImportError(
            "DeepGEMM kernel requires CUDA, but CUDA is not available. Use a different `experts_implementation`."
        )

    # DeepGEMM requires Hopper (SM90) or newer for FP8 WGMMA instructions
    major = torch.cuda.get_device_capability()[0]
    if major < 9:
        raise ImportError(
            f"DeepGEMM requires a Hopper (SM90+) or newer GPU, but the current device "
            f"has compute capability {major}.x. Use a different `experts_implementation`."
        )

    # DeepGEMM requires CUDA runtime ≥ 12.3.
    cuda_major, cuda_minor = get_cuda_runtime_version()
    if cuda_major < 12 or (cuda_major == 12 and cuda_minor < 3):
        raise ImportError(
            f"DeepGEMM requires CUDA runtime 12.3+, but found {cuda_major}.{cuda_minor}. "
            "Please upgrade your CUDA toolkit or use a different `experts_implementation`."
        )

    kernel = lazy_load_kernel("deep-gemm")
    deepgemm_fp8_matmul = getattr(kernel, "fp8_gemm_nt")
    deepgemm_grouped_fp8_matmul = getattr(kernel, "m_grouped_fp8_gemm_nt_contiguous")
    deepgemm_per_token_cast_to_fp8 = resolve_internal_import(kernel, chained_path="utils.per_token_cast_to_fp8")

    missing = [
        name
        for name, attr in [
            ("fp8_gemm_nt", deepgemm_fp8_matmul),
            ("m_grouped_fp8_gemm_nt_contiguous", deepgemm_grouped_fp8_matmul),
            ("utils.per_token_cast_to_fp8", deepgemm_per_token_cast_to_fp8),
        ]
        if attr is None
    ]
    if missing:
        raise ImportError(
            f"DeepGEMM kernel is missing required functions: {', '.join(missing)}. "
            "Please update the `kernels` package (`pip install -U kernels`)."
        )

    _deepgemm_available = True