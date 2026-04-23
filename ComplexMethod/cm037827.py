def select_nvfp4_moe_backend(
    config: FusedMoEConfig,
    weight_key: QuantKey | None,
    activation_key: QuantKey | None,
) -> tuple[NvFp4MoeBackend, type[mk.FusedMoEExperts]]:
    """
    Select the primary NvFP4 MoE backend
    Note: Shape-specific fallbacks may still occur at runtime.
    """

    # NOTE: the kernels are selected in the following order.
    AVAILABLE_BACKENDS = [
        NvFp4MoeBackend.FLASHINFER_TRTLLM,
        NvFp4MoeBackend.FLASHINFER_CUTEDSL,
        NvFp4MoeBackend.FLASHINFER_CUTEDSL_BATCHED,
        NvFp4MoeBackend.FLASHINFER_CUTLASS,
        NvFp4MoeBackend.VLLM_CUTLASS,
        NvFp4MoeBackend.MARLIN,
        NvFp4MoeBackend.EMULATION,
    ]

    # NOTE(rob): this is kind of a hack. We need to peak into
    # the prepare-finalize selection to determine if we are using
    # the batched or standard expert format.
    use_batched = config.moe_parallel_config.use_deepep_ll_kernels
    activation_format = (
        mk.FusedMoEActivationFormat.BatchedExperts
        if use_batched
        else mk.FusedMoEActivationFormat.Standard
    )

    def _make_log_backend(backend: NvFp4MoeBackend):
        available_backend_strs = [b.value for b in AVAILABLE_BACKENDS]
        return (
            f"Using '{backend.value}' NvFp4 MoE backend out "
            f"of potential backends: {available_backend_strs}."
        )

    def _make_log_unsupported(backend: NvFp4MoeBackend, reason: str | None) -> str:
        if reason:
            return (
                f"NvFp4 MoE backend '{backend.value}' does not support the "
                f"deployment configuration since {reason}."
            )
        else:
            return (
                f"NvFp4 MoE backend '{backend.value}' does not support the "
                "deployment configuration."
            )

    def _return_or_raise(
        backend: NvFp4MoeBackend,
        config: FusedMoEConfig,
        weight_key: QuantKey | None,
        activation_key: QuantKey | None,
        activation_format: mk.FusedMoEActivationFormat,
    ) -> tuple[NvFp4MoeBackend, type[mk.FusedMoEExperts]]:
        for k_cls in backend_to_kernel_cls(backend):
            supported, reason = k_cls.is_supported_config(
                k_cls, config, weight_key, activation_key, activation_format
            )
            if supported:
                logger.info_once(_make_log_backend(backend))
                return backend, k_cls

        raise ValueError(_make_log_unsupported(backend, reason))

    # Handle explicit moe_backend from user.
    runner_backend = config.moe_backend
    if runner_backend != "auto":
        requested_backend = map_nvfp4_backend(runner_backend)
        # For batched activation format, use batched variant if available.
        if (
            activation_format == mk.FusedMoEActivationFormat.BatchedExperts
            and requested_backend == NvFp4MoeBackend.FLASHINFER_CUTEDSL
        ):
            requested_backend = NvFp4MoeBackend.FLASHINFER_CUTEDSL_BATCHED
        return _return_or_raise(
            requested_backend, config, weight_key, activation_key, activation_format
        )

    if envs.is_set("VLLM_USE_FLASHINFER_MOE_FP4"):
        if not envs.VLLM_USE_FLASHINFER_MOE_FP4:
            # If the user rejects FlashInfer remove those backends.
            for b in FLASHINFER_NVFP4_MOE_BACKENDS:
                AVAILABLE_BACKENDS.remove(b)

        elif envs.is_set("VLLM_FLASHINFER_MOE_BACKEND"):
            # If user is explicit about backend, validate it.
            backend = fi_2_vllm_backend_map[get_flashinfer_moe_backend()]
            return _return_or_raise(
                backend, config, weight_key, activation_key, activation_format
            )
        else:
            # If the user is not explicit about the backend, try each.
            for backend in FLASHINFER_NVFP4_MOE_BACKENDS:
                for k_cls in backend_to_kernel_cls(backend):
                    supported, reason = k_cls.is_supported_config(
                        k_cls,
                        config,
                        weight_key,
                        activation_key,
                        activation_format,
                    )
                    if supported:
                        logger.info_once(_make_log_backend(backend))
                        return backend, k_cls
                    else:
                        logger.debug_once(_make_log_unsupported(backend, reason))

            raise NotImplementedError(
                "Found VLLM_USE_FLASHINFER_MOE_FP4=1, but no "
                "FlashInfer NVFP4 MoE backend supports the configuration."
            )

    if envs.VLLM_TEST_FORCE_FP8_MARLIN:
        backend = NvFp4MoeBackend.MARLIN
        return _return_or_raise(
            backend, config, weight_key, activation_key, activation_format
        )

    # Select kernels in order of backend.
    for backend in AVAILABLE_BACKENDS:
        for k_cls in backend_to_kernel_cls(backend):
            supported, reason = k_cls.is_supported_config(
                k_cls,
                config,
                weight_key,
                activation_key,
                activation_format,
            )

            if supported:
                logger.info_once(_make_log_backend(backend))
                return backend, k_cls
            else:
                logger.debug_once(_make_log_unsupported(backend, reason))

    raise NotImplementedError(
        "No NvFp4 MoE backend supports the deployment configuration."
    )