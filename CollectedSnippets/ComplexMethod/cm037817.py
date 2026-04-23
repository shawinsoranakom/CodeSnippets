def _apply_per_tensor(
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
        # Delay import for non-CUDA.
        import flashinfer

        # Confirm supported activation function.
        assert activation in [MoEActivation.SILU, MoEActivation.RELU2_NO_MUL]

        activation_type = activation_to_flashinfer_int(activation)

        # Confirm Llama-4 routing is proper.
        if self.routing_method_type == RoutingMethodType.Llama4:
            assert apply_router_weight_on_input
        else:
            assert not apply_router_weight_on_input

        # The DeepSeekV3 routing method requires float32 router logits.
        if self.routing_method_type == RoutingMethodType.DeepSeekV3:
            router_logits = router_logits.to(torch.float32)

        # Currently FI requires bfloat16 routing bias.
        # https://github.com/flashinfer-ai/flashinfer/issues/2909
        if e_score_correction_bias is not None:
            e_score_correction_bias = e_score_correction_bias.to(torch.bfloat16)

        out = flashinfer.fused_moe.trtllm_fp8_per_tensor_scale_moe(
            routing_logits=router_logits,
            routing_bias=e_score_correction_bias,
            hidden_states=hidden_states,
            gemm1_weights=w1,
            output1_scales_scalar=self._g1_scale_c,
            output1_scales_gate_scalar=self._g1_alphas,
            gemm2_weights=w2,
            output2_scales_scalar=self._g2_alphas,
            num_experts=global_num_experts,
            top_k=self.topk,
            n_group=num_expert_group or 0,
            topk_group=topk_group or 0,
            intermediate_size=self.intermediate_size_per_partition,
            local_expert_offset=self.ep_rank * self.local_num_experts,
            local_num_experts=self.local_num_experts,
            routed_scaling_factor=routed_scaling_factor,
            use_routing_scales_on_input=apply_router_weight_on_input,
            routing_method_type=self.routing_method_type,
            activation_type=activation_type,
        )
        return out