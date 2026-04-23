def select_unquantized_moe_backend(
    moe_config: FusedMoEConfig,
) -> tuple[UnquantizedMoeBackend, type[mk.FusedMoEExperts] | None]:
    """
    Select the primary Unquantized MoE backend.
    Note: Shape-specific fallbacks may still occur at runtime.
    """

    if current_platform.is_cpu():
        # TODO: migrate to MK structure.
        return UnquantizedMoeBackend.CPU, None

    if current_platform.is_tpu():
        return UnquantizedMoeBackend.TPU, None

    if current_platform.is_out_of_tree():
        return UnquantizedMoeBackend.OOT, None

    if moe_config.is_lora_enabled:
        return UnquantizedMoeBackend.TRITON, backend_to_kernel_cls(
            UnquantizedMoeBackend.TRITON
        )

    # NOTE: the kernels are selected in the following order.
    AVAILABLE_BACKENDS = _get_priority_backends(moe_config)

    # NOTE(rob): We need to peak into the P/F selection to determine
    # if we are using the batched or standard expert format, which
    # if not ideal. Once we unify TP + DP/EP, we can select P/F first.
    activation_format = (
        mk.FusedMoEActivationFormat.BatchedExperts
        if moe_config.moe_parallel_config.use_batched_activation_format
        else mk.FusedMoEActivationFormat.Standard
    )

    def _make_log_backend(backend: UnquantizedMoeBackend) -> str:
        available_strs = [b.value for b in AVAILABLE_BACKENDS]
        return (
            f"Using {backend.value} Unquantized MoE backend out "
            f"of potential backends: {available_strs}."
        )

    def _make_log_unsupported(
        backend: UnquantizedMoeBackend, reason: str | None
    ) -> str:
        if reason:
            return (
                f"Unquantized MoE backend {backend.value} does not support the "
                f"deployment configuration since {reason}."
            )
        return (
            f"Unquantized MoE backend '{backend.value}' does not support the "
            "deployment configuration."
        )

    def _return_or_raise(
        backend: UnquantizedMoeBackend,
        config: FusedMoEConfig,
        activation_format: mk.FusedMoEActivationFormat,
    ) -> tuple[UnquantizedMoeBackend, type[mk.FusedMoEExperts] | None]:
        k_cls = backend_to_kernel_cls(backend)
        supported, reason = k_cls.is_supported_config(
            k_cls, config, None, None, activation_format
        )
        if supported:
            logger.info_once(_make_log_backend(backend))
            return backend, k_cls
        raise ValueError(_make_log_unsupported(backend, reason))

    # LoRA needs Triton's unfused activation/reduction hooks. Selecting the
    # backend here ensures weights stay in a LoRA-compatible layout instead of
    # being permuted for a backend like FlashInfer or AITER during load.
    if moe_config.is_lora_enabled:
        backend = UnquantizedMoeBackend.TRITON
        if activation_format == mk.FusedMoEActivationFormat.BatchedExperts:
            backend = UnquantizedMoeBackend.BATCHED_TRITON
        return _return_or_raise(
            backend,
            moe_config,
            activation_format,
        )

    runner_backend = moe_config.moe_backend
    if runner_backend != "auto":
        requested_backend = map_unquantized_backend(runner_backend)
        if (
            activation_format == mk.FusedMoEActivationFormat.BatchedExperts
            and requested_backend == UnquantizedMoeBackend.TRITON
        ):
            requested_backend = UnquantizedMoeBackend.BATCHED_TRITON

        return _return_or_raise(requested_backend, moe_config, activation_format)

    # Handle explicit FlashInfer FP16 configuration.
    if envs.is_set("VLLM_USE_FLASHINFER_MOE_FP16"):
        if not envs.VLLM_USE_FLASHINFER_MOE_FP16:
            if UnquantizedMoeBackend.FLASHINFER_TRTLLM in AVAILABLE_BACKENDS:
                AVAILABLE_BACKENDS.remove(UnquantizedMoeBackend.FLASHINFER_TRTLLM)
            if UnquantizedMoeBackend.FLASHINFER_CUTLASS in AVAILABLE_BACKENDS:
                AVAILABLE_BACKENDS.remove(UnquantizedMoeBackend.FLASHINFER_CUTLASS)

        elif envs.is_set("VLLM_FLASHINFER_MOE_BACKEND"):
            # If user is explicit about backend, validate it.
            fi_backend = get_flashinfer_moe_backend()
            if fi_backend == FlashinferMoeBackend.CUTLASS:
                backend = UnquantizedMoeBackend.FLASHINFER_CUTLASS
            elif fi_backend == FlashinferMoeBackend.TENSORRT_LLM:
                backend = UnquantizedMoeBackend.FLASHINFER_TRTLLM
            else:
                raise ValueError(
                    f"FlashInfer MOE backend {fi_backend} "
                    "does not support unquantized MoE."
                )
            k_cls = backend_to_kernel_cls(backend)
            return _return_or_raise(backend, moe_config, activation_format)
        else:
            # If the user is not explicit about the backend, try both.
            for backend in [
                UnquantizedMoeBackend.FLASHINFER_TRTLLM,
                UnquantizedMoeBackend.FLASHINFER_CUTLASS,
            ]:
                k_cls = backend_to_kernel_cls(backend)
                supported, reason = k_cls.is_supported_config(
                    k_cls, moe_config, None, None, activation_format
                )
                if supported:
                    logger.info_once(_make_log_backend(backend))
                    return backend, k_cls
                else:
                    logger.debug_once(_make_log_unsupported(backend, reason))

            raise NotImplementedError(
                "Found VLLM_USE_FLASHINFER_MOE_FP16=1, but no "
                "FlashInfer unquantized MoE backend supports the configuration."
            )

    # Handle explicit AITER FP8 configuration.
    if envs.is_set("VLLM_ROCM_USE_AITER") or envs.is_set("VLLM_ROCM_USE_AITER_MOE"):
        if not envs.VLLM_ROCM_USE_AITER or not envs.VLLM_ROCM_USE_AITER_MOE:
            if UnquantizedMoeBackend.AITER in AVAILABLE_BACKENDS:
                AVAILABLE_BACKENDS.remove(UnquantizedMoeBackend.AITER)
        else:
            backend = UnquantizedMoeBackend.AITER
            return _return_or_raise(backend, moe_config, activation_format)

    for backend in AVAILABLE_BACKENDS:
        k_cls = backend_to_kernel_cls(backend)
        supported, reason = k_cls.is_supported_config(
            k_cls, moe_config, None, None, activation_format
        )
        if supported:
            logger.info_once(_make_log_backend(backend))
            return backend, k_cls

        logger.debug_once(_make_log_unsupported(backend, reason))

    raise NotImplementedError(
        "No Unquantized MoE backend supports the deployment configuration."
    )