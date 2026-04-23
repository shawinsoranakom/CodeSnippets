def is_valid_config(config: MoETestConfig) -> tuple[bool, str | None]:
    # routed_input_transform only makes sense with shared_experts (latent MoE)
    # TODO: not sure this is true
    if config.use_routed_input_transform and not config.use_shared_experts:
        return False, "routed_input_transform requires shared_experts"

    # TODO: disable for now
    if config.use_routed_input_transform and config.enable_eplb:
        return False, "routed_input_transform not supported with EPLB."

    # TODO: disable for now
    if config.use_routed_input_transform and config.use_gate:
        return (
            False,
            "routed_input_transform not supported with gate because of "
            "padding problems",
        )

    # TODO: disable for now
    if config.use_routed_input_transform and config.backend in [
        "deepep_low_latency",
        "deepep_high_throughput",
    ]:
        return (
            False,
            "routed_input_transform not supported with DeepEP backends because "
            "of padding problems",
        )

    # routed_input_transform + quantization + high hidden dimensions
    # TODO: Disable >= 2048 for now due to insane errors.
    if (
        config.use_routed_input_transform
        and config.quantization is not None
        and config.k >= 2048
    ):
        return (
            False,
            "routed_input_transform + quantization + higher hidden dimensions "
            "leads to large differences.",
        )

    # gate requires shared_experts (use_overlapped mode)
    # TODO: also not sure this is true
    if config.use_gate and not config.use_shared_experts:
        return False, "gate requires shared_experts (use_overlapped mode)"

    # Skip modelopt_fp4 if not on B100+ (compute capability 10.0+)
    if (
        config.quantization == "modelopt_fp4"
        and not current_platform.has_device_capability(100)
    ):
        return False, "modelopt_fp4 not supported on H100+ GPUs"

    # Skip flashinfer_nvlink if not on H100+ (compute capability 10.0+)
    if (
        config.backend is not None
        and config.backend.startswith("flashinfer_nvlink")
        and not current_platform.has_device_capability(90)
    ):
        return False, "flashinfer_nvlink needs H100+ GPUs"

    # Backend-specific checks
    if config.backend is not None:
        supported_quants = BACKEND_SUPPORTED_QUANTS.get(config.backend)
        if supported_quants is not None and config.quantization not in supported_quants:
            return (
                False,
                f"{config.backend} does not support quantization={config.quantization}",
            )

        if config.backend == "deepep_low_latency":
            from vllm.model_executor.layers.fused_moe.prepare_finalize.deepep_ll import (  # noqa: E501
                DeepEPLLPrepareAndFinalize,
            )

            if config.k not in DeepEPLLPrepareAndFinalize.SUPPORTED_HIDDEN_SIZES:
                return (
                    False,
                    f"Skipping unsupported K {config.k} in {config.backend} w/o EP.",
                )

        if config.backend == "nixl_ep":
            from vllm.model_executor.layers.fused_moe.nixl_ep_prepare_finalize import (  # noqa: E501
                NixlEPPrepareAndFinalize,
            )

            if config.k not in NixlEPPrepareAndFinalize.SUPPORTED_HIDDEN_SIZES:
                return (
                    False,
                    f"Skipping unsupported K {config.k} in {config.backend} w/o EP.",
                )

    if config.backend is not None:
        supports_ep_dp, supports_dp, supports_tp = BACKEND_EP_DP_TP_SUPPORT[
            config.backend
        ]

        if config.tp_size > 1 and not supports_tp:
            return False, f"{config.backend} does not support TP."

        if config.dp_size > 1 and config.ep_size == 1 and not supports_dp:
            return False, f"{config.backend} does not support DP."

        if config.dp_size > 1 and config.ep_size > 1 and not supports_ep_dp:
            return False, f"{config.backend} does not support EP/DP."
    else:
        if config.tp_size > 1 or config.ep_size > 1 or config.dp_size > 1:
            return False, "An all2all backend is required for parallelism."

    if config.enable_eplb:
        if config.ep_size == 1:
            return False, "EPLB requires EP."

        if config.quantization not in EPLB_SUPPORTED_QUANTS:
            return False, f"EPLB not supported with {config.quantization} quantization."

        if config.backend not in EPLB_SUPPORTED_BACKENDS:
            return False, f"EPLB not supported with {config.backend}."

        if config.num_experts % config.dp_size != 0:
            return False, "EPLB requires num_experts divisible by ep_size"

    # Disable fp4 tests until flashinfer is updated or the Dockerfile is
    # modified to install cublasLt.h. See #39525.
    if (
        config.quantization == "modelopt_fp4"
        and current_platform.is_device_capability_family(100)
    ):
        return False, "Temporarily skip until #39525 is resolved"

    return True, None