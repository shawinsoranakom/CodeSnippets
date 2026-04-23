def backend_to_kernel_cls(
    backend: Fp8MoeBackend,
) -> list[type[mk.FusedMoEExperts]]:
    if backend == Fp8MoeBackend.FLASHINFER_TRTLLM:
        from vllm.model_executor.layers.fused_moe.experts.trtllm_fp8_moe import (  # noqa: E501
            TrtLlmFp8ExpertsModular,
            TrtLlmFp8ExpertsMonolithic,
        )

        return [TrtLlmFp8ExpertsMonolithic, TrtLlmFp8ExpertsModular]

    elif backend == Fp8MoeBackend.FLASHINFER_CUTLASS:
        from vllm.model_executor.layers.fused_moe.flashinfer_cutlass_moe import (
            FlashInferExperts,
        )

        return [FlashInferExperts]

    elif backend == Fp8MoeBackend.DEEPGEMM:
        from vllm.model_executor.layers.fused_moe.triton_deep_gemm_moe import (
            TritonOrDeepGemmExperts,
        )

        return [TritonOrDeepGemmExperts]

    elif backend == Fp8MoeBackend.BATCHED_DEEPGEMM:
        from vllm.model_executor.layers.fused_moe.experts.batched_deep_gemm_moe import (
            BatchedDeepGemmExperts,
        )

        return [BatchedDeepGemmExperts]

    elif backend == Fp8MoeBackend.MARLIN:
        from vllm.model_executor.layers.fused_moe.fused_marlin_moe import (
            MarlinExperts,
        )

        return [MarlinExperts]

    elif backend == Fp8MoeBackend.TRITON:
        from vllm.model_executor.layers.fused_moe.fused_moe import (
            TritonExperts,
        )

        return [TritonExperts]

    elif backend == Fp8MoeBackend.BATCHED_TRITON:
        from vllm.model_executor.layers.fused_moe.fused_batched_moe import (
            BatchedTritonExperts,
        )

        return [BatchedTritonExperts]

    elif backend == Fp8MoeBackend.AITER:
        from vllm.model_executor.layers.fused_moe.rocm_aiter_fused_moe import (
            AiterExperts,
        )

        return [AiterExperts]

    elif backend == Fp8MoeBackend.VLLM_CUTLASS:
        from vllm.model_executor.layers.fused_moe.triton_cutlass_moe import (
            TritonOrCutlassExperts,
        )

        return [TritonOrCutlassExperts]

    elif backend == Fp8MoeBackend.BATCHED_VLLM_CUTLASS:
        from vllm.model_executor.layers.fused_moe.cutlass_moe import (
            CutlassBatchedExpertsFp8,
        )

        return [CutlassBatchedExpertsFp8]

    elif backend == Fp8MoeBackend.XPU:
        from vllm.model_executor.layers.fused_moe.xpu_fused_moe import (
            XPUExpertsFp8,
        )

        return [XPUExpertsFp8]

    else:
        raise ValueError(f"Unknown FP8 MoE backend: {backend.value}")