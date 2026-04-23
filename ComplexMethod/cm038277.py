def init_nvfp4_linear_kernel() -> NvFp4LinearKernel:
    """Select and instantiate the best NVFP4 linear kernel for the
    current platform."""
    config = NvFp4LinearLayerConfig()

    # Env-var overrides.
    force_kernel: type[NvFp4LinearKernel] | None = None
    if envs.VLLM_BATCH_INVARIANT:
        logger.info_once(
            "VLLM_BATCH_INVARIANT forces NVFP4 linear to use the "
            "emulation backend for deterministic execution."
        )
        force_kernel = EmulationNvFp4LinearKernel
    elif envs.VLLM_USE_FBGEMM:
        force_kernel = FbgemmNvFp4LinearKernel
    elif envs.VLLM_USE_NVFP4_CT_EMULATIONS:
        force_kernel = EmulationNvFp4LinearKernel
    elif envs.VLLM_NVFP4_GEMM_BACKEND is not None:
        backend_name = envs.VLLM_NVFP4_GEMM_BACKEND
        force_kernel = _NVFP4_BACKEND_TO_KERNEL.get(backend_name)
        if force_kernel is None:
            raise ValueError(
                f"Unknown VLLM_NVFP4_GEMM_BACKEND={backend_name!r}. "
                f"Valid choices: {list(_NVFP4_BACKEND_TO_KERNEL.keys())}"
            )

    if force_kernel is not None:
        is_supported, reason = force_kernel.is_supported()
        if not is_supported:
            raise ValueError(
                f"Forced NVFP4 kernel {force_kernel.__name__} is not "
                f"supported: {reason}"
            )
        logger.info_once("Using %s for NVFP4 GEMM", force_kernel.__name__)
        return force_kernel(config)

    # Auto-select from registry.
    platform = current_platform._enum
    possible = _POSSIBLE_NVFP4_KERNELS.get(platform, [])

    failure_reasons = []
    for kernel_cls in possible:
        if kernel_cls.__name__ in envs.VLLM_DISABLED_KERNELS:
            failure_reasons.append(
                f" {kernel_cls.__name__} disabled by environment variable"
            )
            continue

        is_supported, reason = kernel_cls.is_supported()
        if not is_supported:
            failure_reasons.append(f"{kernel_cls.__name__}: {reason}")
            continue

        can_implement, reason = kernel_cls.can_implement(config)
        if not can_implement:
            failure_reasons.append(f"{kernel_cls.__name__}: {reason}")
            continue

        if kernel_cls is EmulationNvFp4LinearKernel and failure_reasons:
            logger.warning_once(
                "NVFP4 linear falling back to the slow and unoptimized "
                "emulation backend as no optimized backend is available "
                "(unavailable reasons:\n - %s\n). "
                "In case you expect one of these backends to be used, "
                "please verify your environment.",
                "\n - ".join(failure_reasons),
            )

        logger.info_once("Using %s for NVFP4 GEMM", kernel_cls.__name__)
        return kernel_cls(config)

    raise ValueError(
        "Failed to find a kernel that can implement the "
        "NVFP4 linear layer. Reasons: \n" + "\n".join(failure_reasons)
    )