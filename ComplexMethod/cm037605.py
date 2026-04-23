def apply_monolithic(
        self,
        layer: FusedMoE,
        x: torch.Tensor,
        router_logits: torch.Tensor,
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        from flashinfer.fused_moe.core import (
            ActivationType,
            Fp8QuantizationType,
        )

        assert self.mxfp8_backend == Fp8MoeBackend.FLASHINFER_TRTLLM

        if layer.enable_eplb:
            raise NotImplementedError(
                "EPLB is not supported for FlashInfer TRTLLM MXFP8 MoE backend."
            )

        supported_activations = [MoEActivation.SILU]
        if layer.activation not in supported_activations:
            raise NotImplementedError(
                "FlashInfer TRTLLM MXFP8 MoE supports only "
                f"{supported_activations}, got {layer.activation}."
            )

        # Map vLLM MoEActivation to FlashInfer ActivationType.
        activation_map = {
            MoEActivation.SILU: ActivationType.Swiglu,
            MoEActivation.RELU2_NO_MUL: ActivationType.Relu2,
        }
        fi_activation_type: ActivationType = activation_map[layer.activation]

        # DeepSeekV3 routing requires float32 logits; others expect bfloat16.
        if layer.routing_method_type == RoutingMethodType.DeepSeekV3:
            assert router_logits.dtype == torch.float32, (
                "DeepSeekV3 routing requires float32 router_logits, "
                f"got {router_logits.dtype}."
            )
        else:
            router_logits = router_logits.to(torch.bfloat16)

        # Treat 0 as "unset" for compatibility with ungrouped routing configs.
        n_group = layer.num_expert_group or None
        topk_group = layer.topk_group or None

        hidden_states_mxfp8, hidden_states_scale = mxfp8_e4m3_quantize(
            x,
            is_sf_swizzled_layout=False,
        )

        kwargs: dict = dict(
            routing_logits=router_logits,
            routing_bias=layer.e_score_correction_bias,
            hidden_states=hidden_states_mxfp8,
            hidden_states_scale=hidden_states_scale,
            gemm1_weights=layer.w13_weight,
            gemm1_weights_scale=layer.w13_weight_scale,
            gemm2_weights=layer.w2_weight,
            gemm2_weights_scale=layer.w2_weight_scale,
            num_experts=layer.global_num_experts,
            top_k=layer.top_k,
            # Keep Optional semantics: FlashInfer expects None for non-grouped
            # routing (e.g. Qwen3 Renormalize), not 0.
            n_group=n_group,
            topk_group=topk_group,
            intermediate_size=layer.intermediate_size_per_partition,
            local_expert_offset=layer.ep_rank * layer.local_num_experts,
            local_num_experts=layer.local_num_experts,
            routed_scaling_factor=layer.routed_scaling_factor,
            routing_method_type=layer.routing_method_type,
            use_shuffled_weight=True,
            weight_layout=0,
            fp8_quantization_type=Fp8QuantizationType.MxFp8,
        )

        if fi_activation_type != ActivationType.Swiglu:
            raise NotImplementedError(
                "FlashInfer TRTLLM MXFP8 MoE supports only Swiglu activation, "
                f"got {fi_activation_type}."
            )

        return flashinfer_trtllm_fp8_block_scale_moe(**kwargs)