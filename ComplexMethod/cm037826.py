def backend_to_kernel_cls(
    backend: NvFp4MoeBackend,
) -> list[type[mk.FusedMoEExperts]]:
    if backend == NvFp4MoeBackend.FLASHINFER_TRTLLM:
        from vllm.model_executor.layers.fused_moe.experts.trtllm_nvfp4_moe import (
            TrtLlmNvFp4ExpertsModular,
            TrtLlmNvFp4ExpertsMonolithic,
        )

        # NOTE: prefer Monolthic > Modular, so return Monolithic first.
        return [
            TrtLlmNvFp4ExpertsMonolithic,
            TrtLlmNvFp4ExpertsModular,
        ]

    elif backend == NvFp4MoeBackend.FLASHINFER_CUTLASS:
        from vllm.model_executor.layers.fused_moe.flashinfer_cutlass_moe import (
            FlashInferExperts,
        )

        return [FlashInferExperts]

    elif backend == NvFp4MoeBackend.FLASHINFER_CUTEDSL:
        from vllm.model_executor.layers.fused_moe.experts.flashinfer_cutedsl_moe import (  # noqa: E501
            FlashInferCuteDSLExperts,
        )

        return [FlashInferCuteDSLExperts]

    elif backend == NvFp4MoeBackend.FLASHINFER_CUTEDSL_BATCHED:
        from vllm.model_executor.layers.fused_moe.experts.flashinfer_cutedsl_batched_moe import (  # noqa: E501
            FlashInferCuteDSLBatchedExperts,
        )

        return [FlashInferCuteDSLBatchedExperts]

    elif backend == NvFp4MoeBackend.VLLM_CUTLASS:
        from vllm.model_executor.layers.fused_moe.cutlass_moe import (
            CutlassExpertsFp4,
        )

        return [CutlassExpertsFp4]

    elif backend == NvFp4MoeBackend.MARLIN:
        from vllm.model_executor.layers.fused_moe.fused_marlin_moe import (
            MarlinExperts,
        )

        return [MarlinExperts]
    elif backend == NvFp4MoeBackend.EMULATION:
        from vllm.model_executor.layers.fused_moe.experts.nvfp4_emulation_moe import (
            Nvfp4QuantizationEmulationTritonExperts,
        )

        return [Nvfp4QuantizationEmulationTritonExperts]
    else:
        raise ValueError(f"Unknown NvFP4 MoE backend: {backend.value}")