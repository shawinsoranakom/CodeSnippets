def use_cutlass_template(layout: Layout, m: int, n: int, k: int) -> bool:
    from .virtualized import V

    # TODO: Enable CUTLASS in non-AOT cpp_wrapper mode. The CUTLASS
    # codegen (CUDATemplateKernel.call_kernel) already has cpp_wrapper-aware
    # arg handling, but the other half is missing: the non-triton branch of
    # CppWrapperGpu._generate_kernel_call_helper unconditionally emits
    # `kernels.<name>(...)`, and that AOTInductorModelKernels struct only
    # exists in AOT mode. Fixing this requires adding dlopen/dlsym loading
    # for the compiled CUTLASS .so, similar to how the triton branch uses
    # static CUfunction + loadKernel for non-AOT mode.
    if V.graph.cpp_wrapper and not V.graph.aot_mode:
        warnings.warn(
            "CUTLASS backend is not supported with non-AOT cpp_wrapper mode. "
            "Skipping CUTLASS backend.",
        )
        return False

    gemm_size = V.graph.sizevars.optimization_hint(m * n * k, fallback=-1)
    if gemm_size <= 0 or gemm_size < config.cutlass.cutlass_backend_min_gemm_size:
        return False
    from .codegen.cutlass.utils import try_import_cutlass

    # Do not use cutlass template on ROCm
    if torch.version.hip:
        return False

    # output dtype
    # FP32 not supported: https://github.com/pytorch/pytorch/issues/145952
    layout_dtypes = [torch.float16, torch.bfloat16, torch.int32]
    res = (
        _use_template_for_gpu(layout, layout_dtypes)
        and (config.max_autotune or config.max_autotune_gemm)
        and _use_autotune_backend("CUTLASS")
    )

    if res:
        if not try_import_cutlass():
            log.warning(
                "Failed to import CUTLASS lib. Please check whether "
                "_inductor.config.cutlass.cutlass_dir %s is set correctly. "
                "Skipping CUTLASS backend for now.",
                config.cutlass.cutlass_dir,
            )
            return False
    return res