def select_gemm_impl(
        self,
        prepare_finalize,
        layer: torch.nn.Module,
    ):
        """
        Select the GEMM implementation for GPTQ-Marlin MoE.

        Returns MarlinExperts configured for GPTQ quantization.
        This is ONLY used when LoRA is enabled.
        Without LoRA, GPTQ uses its own apply() method.
        """
        # Only use modular kernels when LoRA is enabled
        # Without LoRA, GPTQ's own apply() method works fine and is more efficient
        if not self.moe.is_lora_enabled:
            raise NotImplementedError(
                "GPTQ-Marlin uses its own apply() method when LoRA is not enabled. "
                "Modular kernels are only used for LoRA support."
            )

        # The modular marlin kernels do not support 8-bit weights.
        if self.quant_config.weight_bits == 8:
            raise NotImplementedError(
                "GPTQ-Marlin kernel does not support 8-bit weights."
            )

        from vllm.model_executor.layers.fused_moe import modular_kernel as mk
        from vllm.model_executor.layers.fused_moe.fused_marlin_moe import (
            BatchedMarlinExperts,
            MarlinExperts,
        )

        # Ensure quant config is initialized
        assert self.moe_quant_config is not None, (
            "moe_quant_config must be initialized before select_gemm_impl"
        )

        w13_g_idx = (
            getattr(layer, "w13_g_idx", None) if self.quant_config.desc_act else None
        )
        w2_g_idx = (
            getattr(layer, "w2_g_idx", None) if self.quant_config.desc_act else None
        )
        w13_g_idx_sort_indices = (
            getattr(layer, "w13_g_idx_sort_indices", None)
            if self.quant_config.desc_act
            else None
        )
        w2_g_idx_sort_indices = (
            getattr(layer, "w2_g_idx_sort_indices", None)
            if self.quant_config.desc_act
            else None
        )

        # Check if using batched expert format (for Expert Parallelism)
        if (
            prepare_finalize.activation_format
            == mk.FusedMoEActivationFormat.BatchedExperts
        ):
            # For batched format, use BatchedMarlinExperts
            max_num_tokens_per_rank = prepare_finalize.max_num_tokens_per_rank()
            assert max_num_tokens_per_rank is not None
            return BatchedMarlinExperts(
                max_num_tokens=max_num_tokens_per_rank,
                num_dispatchers=prepare_finalize.num_dispatchers(),
                moe_config=self.moe,
                quant_config=self.moe_quant_config,
                w13_g_idx=w13_g_idx,
                w2_g_idx=w2_g_idx,
                w13_g_idx_sort_indices=w13_g_idx_sort_indices,
                w2_g_idx_sort_indices=w2_g_idx_sort_indices,
                is_k_full=self.is_k_full,
            )
        else:
            # Standard Marlin experts for GPTQ
            return MarlinExperts(
                moe_config=self.moe,
                quant_config=self.moe_quant_config,
                w13_g_idx=w13_g_idx,
                w2_g_idx=w2_g_idx,
                w13_g_idx_sort_indices=w13_g_idx_sort_indices,
                w2_g_idx_sort_indices=w2_g_idx_sort_indices,
                is_k_full=self.is_k_full,
            )