def select_fp8_moe_backend(
    config: FusedMoEConfig,
    weight_key: QuantKey | None,
    activation_key: QuantKey | None,
    allow_vllm_cutlass: bool = False,
) -> tuple[Fp8MoeBackend, type[mk.FusedMoEExperts] | None]:
    """
    Select the primary FP8 MoE backend
    Note: Shape-specific fallbacks may still occur at runtime.
    """

    if config.is_lora_enabled:
        return Fp8MoeBackend.TRITON, backend_to_kernel_cls(Fp8MoeBackend.TRITON)[0]

    # NOTE: the kernels are selected in the following order.
    AVAILABLE_BACKENDS = _get_priority_backends(config, weight_key, activation_key)

    # NOTE(rob): We need to peak into the P/F selection to determine
    # if we are using the batched or standard expert format, which
    # if not ideal. Once we unify TP + DP/EP, we can select P/F first.
    activation_format = (
        mk.FusedMoEActivationFormat.BatchedExperts
        if config.moe_parallel_config.use_batched_activation_format
        else mk.FusedMoEActivationFormat.Standard
    )

    def _make_log_backend(backend: Fp8MoeBackend):
        available_backend_strs = [b.value for b in AVAILABLE_BACKENDS]
        return (
            f"Using {backend.value} Fp8 MoE backend out "
            f"of potential backends: {available_backend_strs}."
        )

    def _make_log_unsupported(backend: Fp8MoeBackend, reason: str | None) -> str:
        if reason:
            return (
                f"FP8 MoE backend {backend.value} does not support the "
                f"deployment configuration since {reason}."
            )
        else:
            return (
                f"FP8 MoE backend '{backend.value}' does not support the "
                "deployment configuration."
            )

    def _return_or_raise(
        backend: Fp8MoeBackend,
        config: FusedMoEConfig,
        weight_key: QuantKey | None,
        activation_key: QuantKey | None,
        activation_format: mk.FusedMoEActivationFormat,
    ) -> tuple[Fp8MoeBackend, type[mk.FusedMoEExperts]]:
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
        requested_backend = map_fp8_backend(runner_backend)
        # For batched activation format, use batched variants if available.
        if activation_format == mk.FusedMoEActivationFormat.BatchedExperts:
            if requested_backend == Fp8MoeBackend.DEEPGEMM:
                requested_backend = Fp8MoeBackend.BATCHED_DEEPGEMM
            elif requested_backend == Fp8MoeBackend.TRITON:
                requested_backend = Fp8MoeBackend.BATCHED_TRITON
            elif requested_backend == Fp8MoeBackend.VLLM_CUTLASS:
                requested_backend = Fp8MoeBackend.BATCHED_VLLM_CUTLASS

        if (
            requested_backend
            in [
                Fp8MoeBackend.VLLM_CUTLASS,
                Fp8MoeBackend.BATCHED_VLLM_CUTLASS,
            ]
            and not allow_vllm_cutlass
        ):
            raise ValueError(
                "vLLM CUTLASS FP8 MoE backend is disabled for this configuration."
            )

        return _return_or_raise(
            requested_backend, config, weight_key, activation_key, activation_format
        )

    # Handle explicit FlashInfer FP8 configuration.
    if envs.is_set("VLLM_USE_FLASHINFER_MOE_FP8"):
        if not envs.VLLM_USE_FLASHINFER_MOE_FP8:
            # If the user rejects FlashInfer remove those backends.
            AVAILABLE_BACKENDS.remove(Fp8MoeBackend.FLASHINFER_TRTLLM)
            AVAILABLE_BACKENDS.remove(Fp8MoeBackend.FLASHINFER_CUTLASS)

        elif envs.is_set("VLLM_FLASHINFER_MOE_BACKEND"):
            # If user is explicit about backend, validate it.
            fi_backend = get_flashinfer_moe_backend()
            if fi_backend == FlashinferMoeBackend.CUTLASS:
                backend = Fp8MoeBackend.FLASHINFER_CUTLASS
            elif fi_backend == FlashinferMoeBackend.TENSORRT_LLM:
                backend = Fp8MoeBackend.FLASHINFER_TRTLLM
            else:
                raise ValueError(
                    f"FlashInfer MOE backend {fi_backend} does not support FP8 MoE."
                )
            k_cls = backend_to_kernel_cls(backend)[0]
            return _return_or_raise(
                backend, config, weight_key, activation_key, activation_format
            )
        else:
            # If the user is not explicit about the backend, try both.
            for backend in [
                Fp8MoeBackend.FLASHINFER_TRTLLM,
                Fp8MoeBackend.FLASHINFER_CUTLASS,
            ]:
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
                "Found VLLM_USE_FLASHINFER_MOE_FP8=1, but no "
                "FlashInfer FP8 MoE backend supports the configuration."
            )

    # Handle explicit DeepGEMM FP8 configuration.
    if envs.is_set("VLLM_USE_DEEP_GEMM") or envs.is_set("VLLM_MOE_USE_DEEP_GEMM"):
        if not envs.VLLM_USE_DEEP_GEMM or not envs.VLLM_MOE_USE_DEEP_GEMM:
            AVAILABLE_BACKENDS.remove(Fp8MoeBackend.DEEPGEMM)
            AVAILABLE_BACKENDS.remove(Fp8MoeBackend.BATCHED_DEEPGEMM)
        else:
            backend = (
                Fp8MoeBackend.DEEPGEMM
                if activation_format == mk.FusedMoEActivationFormat.Standard
                else Fp8MoeBackend.BATCHED_DEEPGEMM
            )
            return _return_or_raise(
                backend, config, weight_key, activation_key, activation_format
            )

    # Handle explicit MARLIN FP8 configuration.
    if envs.VLLM_TEST_FORCE_FP8_MARLIN:
        backend = Fp8MoeBackend.MARLIN
        return _return_or_raise(
            backend, config, weight_key, activation_key, activation_format
        )

    # Handle explicit AITER FP8 configuration.
    if envs.is_set("VLLM_ROCM_USE_AITER") or envs.is_set("VLLM_ROCM_USE_AITER_MOE"):
        if not envs.VLLM_ROCM_USE_AITER or not envs.VLLM_ROCM_USE_AITER_MOE:
            AVAILABLE_BACKENDS.remove(Fp8MoeBackend.AITER)
        else:
            backend = Fp8MoeBackend.AITER
            return _return_or_raise(
                backend, config, weight_key, activation_key, activation_format
            )

    if not allow_vllm_cutlass:
        AVAILABLE_BACKENDS.remove(Fp8MoeBackend.VLLM_CUTLASS)
        AVAILABLE_BACKENDS.remove(Fp8MoeBackend.BATCHED_VLLM_CUTLASS)

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

    # TODO(rob): per discussion with TPU team, we need a way to register
    # MoE backends by OOT plugins, rather than having an explicit list
    # of AVAILABLE_BACKENDS. Enabling returning `Fp8MoeBackend.NONE` is
    # a temporary measure until these register APIs are complete.
    if current_platform.is_cuda() or current_platform.is_rocm():
        raise NotImplementedError(
            "No FP8 MoE backend supports the deployment configuration."
        )

    return Fp8MoeBackend.NONE, None