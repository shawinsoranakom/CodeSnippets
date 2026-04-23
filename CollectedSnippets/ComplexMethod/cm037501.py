def apply_config_platform_defaults(cls, vllm_config: "VllmConfig") -> None:
        from vllm._aiter_ops import rocm_aiter_ops
        from vllm.config.compilation import CUDAGraphMode

        compilation_config = vllm_config.compilation_config
        is_eager_execution = compilation_config.cudagraph_mode == CUDAGraphMode.NONE
        use_aiter_fused_moe = rocm_aiter_ops.is_fused_moe_enabled()
        use_aiter_rms_norm = rocm_aiter_ops.is_rmsnorm_enabled()
        use_aiter_fp8_linear = rocm_aiter_ops.is_linear_fp8_enabled()
        use_aiter_fused_se = rocm_aiter_ops.is_fusion_moe_shared_experts_enabled()
        #  Aiter rms norm perform best when CUDA Graph capture is enabled.
        if (
            use_aiter_rms_norm
            and not is_eager_execution
            and "-rms_norm" not in compilation_config.custom_ops
        ):
            compilation_config.custom_ops.append("+rms_norm")

        if use_aiter_fp8_linear and "-quant_fp8" not in compilation_config.custom_ops:
            compilation_config.custom_ops.append("+quant_fp8")

        if use_aiter_fused_se and "-grouped_topk" in compilation_config.custom_ops:
            logger.warning_once(
                "VLLM_ROCM_USE_AITER_FUSION_SHARED_EXPERTS is enabled, which "
                "requires the 'grouped_topk' custom op. Overriding the "
                "user-provided '-grouped_topk'."
            )
            compilation_config.custom_ops.remove("-grouped_topk")
        # Ensure grouped_topk is always enabled when using AITER if
        # its not disabled by user
        if (
            use_aiter_fused_moe
            and "+grouped_topk" not in compilation_config.custom_ops
            and "-grouped_topk" not in compilation_config.custom_ops
        ):
            compilation_config.custom_ops.append("+grouped_topk")

        # Default dispatch to rocm's sparse_attn_indexer implementation
        compilation_config.custom_ops.append("+sparse_attn_indexer")