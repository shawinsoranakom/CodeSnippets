def _apply_block_scale(
        self,
        hidden_states: torch.Tensor,
        w1: torch.Tensor,
        w2: torch.Tensor,
        router_logits: torch.Tensor,
        activation: MoEActivation,
        global_num_experts: int,
        expert_map: torch.Tensor | None,
        a1q_scale: torch.Tensor | None,
        apply_router_weight_on_input: bool,
        # grouped topk + fused topk bias parameters
        num_expert_group: int | None = None,
        e_score_correction_bias: torch.Tensor | None = None,
        routed_scaling_factor: float | None = None,
        topk_group: int | None = None,
    ) -> torch.Tensor:
        import flashinfer
        from flashinfer.fused_moe import Fp8QuantizationType, WeightLayout

        assert not apply_router_weight_on_input
        assert activation == MoEActivation.SILU
        assert self.topk <= global_num_experts
        assert self.topk <= 10
        assert global_num_experts % 4 == 0
        assert self.quant_config.block_shape in [[128, 128], [1, 32]]
        # Kernel expects #experts <= #threads 512
        assert global_num_experts <= 512
        # TODO: fuse into the quant kernel.
        assert a1q_scale is not None

        if self.routing_method_type == RoutingMethodType.DeepSeekV3:
            router_logits = router_logits.to(torch.float32)

        # Currently FI requires bfloat16 routing bias.
        # https://github.com/flashinfer-ai/flashinfer/issues/2909
        if e_score_correction_bias is not None:
            e_score_correction_bias = e_score_correction_bias.to(torch.bfloat16)

        is_mxfp8 = self.quant_config.block_shape == [1, 32]
        if is_mxfp8:
            fp8_quant_type = Fp8QuantizationType.MxFp8
            use_shuffled_weight = True
            weight_layout = WeightLayout.MajorK
            hidden_states_scale = a1q_scale
        else:
            fp8_quant_type = Fp8QuantizationType.DeepSeekFp8
            use_shuffled_weight = True
            weight_layout = WeightLayout.BlockMajorK
            hidden_states_scale = a1q_scale.t().contiguous()

        return flashinfer.fused_moe.trtllm_fp8_block_scale_moe(
            routing_logits=router_logits,
            routing_bias=e_score_correction_bias,
            hidden_states=hidden_states,
            hidden_states_scale=hidden_states_scale,
            gemm1_weights=w1,
            gemm1_weights_scale=self.quant_config.w1_scale,
            gemm2_weights=w2,
            gemm2_weights_scale=self.quant_config.w2_scale,
            num_experts=global_num_experts,
            top_k=self.topk,
            n_group=(num_expert_group or 0),
            topk_group=(topk_group or 0),
            intermediate_size=self.intermediate_size_per_partition,
            local_expert_offset=self.ep_rank * self.local_num_experts,
            local_num_experts=self.local_num_experts,
            routed_scaling_factor=routed_scaling_factor,
            routing_method_type=self.routing_method_type,
            use_shuffled_weight=use_shuffled_weight,
            weight_layout=weight_layout,
            fp8_quantization_type=fp8_quant_type,
        )