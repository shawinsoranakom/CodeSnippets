def select_gpt_oss_mxfp4_moe_backend(
    config: FusedMoEConfig,
) -> tuple[Mxfp4MoeBackend, type[mk.FusedMoEExperts] | None]:
    """
    Select the primary MXFP4 MoE backend.
    Note: Shape-specific fallbacks may still occur at runtime.
    """
    device_capability = current_platform.get_device_capability()
    triton_kernels_supported = (
        has_triton_kernels()
        and device_capability is not None
        and (9, 0) <= device_capability < (11, 0)
    )

    # LoRA: separate experts backend path
    if config.is_lora_enabled:
        if not current_platform.is_cuda():
            # ROCm: Triton mxfp4 LoRA hits GPU memory faults due to
            # triton_kernels.tensor.Tensor / HIP read-only page issues
            # during weight swizzle and LoRA forward. Needs work from
            # the triton_kernels/aiter side.
            raise NotImplementedError("Mxfp4 LoRA is currently only supported on CUDA.")
        if envs.VLLM_MXFP4_USE_MARLIN is False and triton_kernels_supported:
            logger.info_once("Using Triton backend for mxfp4 lora")
            return Mxfp4MoeBackend.TRITON_UNFUSED, backend_to_kernel_cls(
                Mxfp4MoeBackend.TRITON_UNFUSED
            )[0]
        logger.info_once("Using Marlin backend for mxfp4 lora")
        return Mxfp4MoeBackend.MARLIN, backend_to_kernel_cls(Mxfp4MoeBackend.MARLIN)[0]

    activation_format = (
        mk.FusedMoEActivationFormat.BatchedExperts
        if config.moe_parallel_config.use_batched_activation_format
        else mk.FusedMoEActivationFormat.Standard
    )

    def _make_log_backend(backend: Mxfp4MoeBackend):
        return f"Using '{backend.value}' Mxfp4 MoE backend."

    def _make_log_unsupported(backend: Mxfp4MoeBackend, reason: str | None) -> str:
        if reason:
            return (
                f"Mxfp4 MoE backend '{backend.value}' does not support the "
                f"deployment configuration since {reason}."
            )
        return (
            f"Mxfp4 MoE backend '{backend.value}' does not support the "
            "deployment configuration."
        )

    def _return_or_raise(
        backend: Mxfp4MoeBackend,
        config: FusedMoEConfig,
        weight_key: QuantKey | None,
        activation_key: QuantKey | None,
        activation_format: mk.FusedMoEActivationFormat,
    ) -> tuple[Mxfp4MoeBackend, type[mk.FusedMoEExperts]]:
        reason: str | None = None
        for k_cls in backend_to_kernel_cls(backend):
            supported, reason = k_cls.is_supported_config(
                k_cls, config, weight_key, activation_key, activation_format
            )
            if supported:
                logger.info_once(_make_log_backend(backend))
                return backend, k_cls
        raise ValueError(_make_log_unsupported(backend, reason))

    runner_backend = config.moe_backend
    if runner_backend != "auto":
        requested_backend = map_mxfp4_backend(runner_backend)
        if (
            activation_format == mk.FusedMoEActivationFormat.BatchedExperts
            and requested_backend == Mxfp4MoeBackend.MARLIN
        ):
            requested_backend = Mxfp4MoeBackend.BATCHED_MARLIN
        return _return_or_raise(
            requested_backend,
            config,
            kMxfp4Static,
            _backend_activation_key(requested_backend),
            activation_format,
        )

    # Select kernels in order of backend.
    AVAILABLE_BACKENDS = _get_priority_backends()

    # Handle explicit FlashInfer MXFP4 BF16 configuration.
    if envs.is_set("VLLM_USE_FLASHINFER_MOE_MXFP4_BF16"):
        if not envs.VLLM_USE_FLASHINFER_MOE_MXFP4_BF16:
            AVAILABLE_BACKENDS.remove(Mxfp4MoeBackend.FLASHINFER_TRTLLM_MXFP4_BF16)
            AVAILABLE_BACKENDS.remove(Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_BF16)
        else:
            if current_platform.is_device_capability(90):
                return _return_or_raise(
                    Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_BF16,
                    config,
                    kMxfp4Static,
                    None,
                    activation_format,
                )
            if current_platform.is_device_capability_family(100):
                return _return_or_raise(
                    Mxfp4MoeBackend.FLASHINFER_TRTLLM_MXFP4_BF16,
                    config,
                    kMxfp4Static,
                    None,
                    activation_format,
                )
            raise ValueError(
                "VLLM_USE_FLASHINFER_MOE_MXFP4_BF16=1 is set but the "
                "current device capability is not supported. "
                "Only SM90 (CUTLASS) and SM100+ (TRTLLM) are supported."
            )

    # Handle explicit FlashInfer MXFP4 MXFP8 TRTLLM configuration.
    if (
        envs.is_set("VLLM_USE_FLASHINFER_MOE_MXFP4_MXFP8")
        and envs.VLLM_USE_FLASHINFER_MOE_MXFP4_MXFP8
    ):
        return _return_or_raise(
            Mxfp4MoeBackend.FLASHINFER_TRTLLM_MXFP4_MXFP8,
            config,
            kMxfp4Static,
            kMxfp8Dynamic,
            activation_format,
        )

    # Handle explicit FlashInfer MXFP4 MXFP8 CUTLASS configuration.
    if (
        envs.is_set("VLLM_USE_FLASHINFER_MOE_MXFP4_MXFP8_CUTLASS")
        and envs.VLLM_USE_FLASHINFER_MOE_MXFP4_MXFP8_CUTLASS
    ):
        return _return_or_raise(
            Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_MXFP8,
            config,
            kMxfp4Static,
            kMxfp8Dynamic,
            activation_format,
        )

    # Handle explicit Marlin MXFP4 configuration.
    if envs.is_set("VLLM_MXFP4_USE_MARLIN") and envs.VLLM_MXFP4_USE_MARLIN:
        return _return_or_raise(
            Mxfp4MoeBackend.MARLIN,
            config,
            kMxfp4Static,
            None,
            activation_format,
        )

    for backend in AVAILABLE_BACKENDS:
        activation_key = _backend_activation_key(backend)
        for k_cls in backend_to_kernel_cls(backend):
            supported, reason = k_cls.is_supported_config(
                k_cls, config, kMxfp4Static, activation_key, activation_format
            )
            if supported:
                logger.info_once(_make_log_backend(backend))
                return backend, k_cls
            else:
                logger.debug_once(_make_log_unsupported(backend, reason))

    if current_platform.is_xpu():
        backend = Mxfp4MoeBackend.XPU
        logger.info_once(_make_log_backend(backend))
        return _return_or_raise(
            Mxfp4MoeBackend.XPU,
            config,
            kMxfp4Static,
            None,
            activation_format,
        )

    if current_platform.is_cuda() or current_platform.is_rocm():
        raise NotImplementedError(
            "No MXFP4 MoE backend supports the deployment configuration."
        )

    return Mxfp4MoeBackend.NONE, None