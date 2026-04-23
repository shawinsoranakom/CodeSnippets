def backend_to_kernel_cls(
    backend: Mxfp4MoeBackend,
) -> list[type[mk.FusedMoEExperts]]:
    if backend in (
        Mxfp4MoeBackend.FLASHINFER_TRTLLM_MXFP4_BF16,
        Mxfp4MoeBackend.FLASHINFER_TRTLLM_MXFP4_MXFP8,
    ):
        from vllm.model_executor.layers.fused_moe.experts.trtllm_mxfp4_moe import (
            TrtLlmMxfp4ExpertsModular,
            TrtLlmMxfp4ExpertsMonolithic,
        )

        # NOTE: prefer Monolithic > Modular, so return Monolithic first.
        return [TrtLlmMxfp4ExpertsMonolithic, TrtLlmMxfp4ExpertsModular]

    elif backend in (
        Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_BF16,
        Mxfp4MoeBackend.FLASHINFER_CUTLASS_MXFP4_MXFP8,
    ):
        from vllm.model_executor.layers.fused_moe.flashinfer_cutlass_moe import (
            FlashInferExperts,
        )

        return [FlashInferExperts]

    elif backend == Mxfp4MoeBackend.TRITON:
        from vllm.model_executor.layers.fused_moe.experts.gpt_oss_triton_kernels_moe import (  # noqa: E501
            OAITritonExperts,
            OAITritonMxfp4ExpertsMonolithic,
        )

        # NOTE: prefer Monolithic > Modular, so return Monolithic first.
        return [OAITritonMxfp4ExpertsMonolithic, OAITritonExperts]

    elif backend == Mxfp4MoeBackend.TRITON_UNFUSED:
        from vllm.model_executor.layers.fused_moe.experts.gpt_oss_triton_kernels_moe import (  # noqa: E501
            UnfusedOAITritonExperts,
        )

        return [UnfusedOAITritonExperts]

    elif backend == Mxfp4MoeBackend.MARLIN:
        from vllm.model_executor.layers.fused_moe.fused_marlin_moe import (
            MarlinExperts,
        )

        return [MarlinExperts]

    elif backend == Mxfp4MoeBackend.BATCHED_MARLIN:
        from vllm.model_executor.layers.fused_moe.fused_marlin_moe import (
            BatchedMarlinExperts,
        )

        return [BatchedMarlinExperts]

    elif backend == Mxfp4MoeBackend.AITER:
        from vllm.model_executor.layers.fused_moe.rocm_aiter_fused_moe import (
            AiterExperts,
        )

        return [AiterExperts]

    elif backend == Mxfp4MoeBackend.XPU:
        from vllm.model_executor.layers.fused_moe.xpu_fused_moe import XPUExpertsMXFp4

        return [XPUExpertsMXFp4]

    elif backend == Mxfp4MoeBackend.EMULATION:
        from vllm.model_executor.layers.fused_moe.experts.ocp_mx_emulation_moe import (
            OCP_MXQuantizationEmulationTritonExperts,
        )

        return [OCP_MXQuantizationEmulationTritonExperts]

    else:
        raise ValueError(f"Unknown MXFP4 MoE backend: {backend.value}")