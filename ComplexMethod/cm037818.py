def apply(
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

        assert activation in [MoEActivation.SILU, MoEActivation.RELU2_NO_MUL]
        assert a1q_scale is not None
        assert self.quant_config.w1_scale is not None
        assert self.quant_config.w2_scale is not None
        assert (
            apply_router_weight_on_input
            and self.routing_method_type == RoutingMethodType.Llama4
        ) or (
            not apply_router_weight_on_input
            and self.routing_method_type != RoutingMethodType.Llama4
        )

        # Prepare router logits for kernel format.
        router_logits = (
            router_logits.to(torch.float32)
            if self.routing_method_type == RoutingMethodType.DeepSeekV3
            else router_logits
        )

        # Currently FI requires bfloat16 routing bias.
        # https://github.com/flashinfer-ai/flashinfer/issues/2909
        if e_score_correction_bias is not None:
            e_score_correction_bias = e_score_correction_bias.to(torch.bfloat16)

        # Invoke kernel.
        # NOTE: Activation padding and output
        # truncation are handled by the MoE runner's
        return flashinfer.fused_moe.trtllm_fp4_block_scale_moe(
            routing_logits=router_logits,
            routing_bias=e_score_correction_bias,
            hidden_states=hidden_states,
            hidden_states_scale=a1q_scale.view(torch.float8_e4m3fn).reshape(
                *hidden_states.shape[:-1], -1
            ),
            gemm1_weights=w1,
            gemm1_weights_scale=self.quant_config.w1_scale.view(torch.float8_e4m3fn),
            gemm1_bias=None,
            gemm1_alpha=None,
            gemm1_beta=None,
            gemm1_clamp_limit=None,
            gemm2_weights=w2,
            gemm2_weights_scale=self.quant_config.w2_scale.view(torch.float8_e4m3fn),
            gemm2_bias=None,
            output1_scale_scalar=self.g1_scale_c,
            output1_scale_gate_scalar=self.quant_config.g1_alphas,
            output2_scale_scalar=self.quant_config.g2_alphas,
            num_experts=global_num_experts,
            top_k=self.topk,
            n_group=(num_expert_group or 0),
            topk_group=(topk_group or 0),
            intermediate_size=self.intermediate_size_per_partition,
            local_expert_offset=self.ep_rank * self.local_num_experts,
            local_num_experts=self.local_num_experts,
            routed_scaling_factor=routed_scaling_factor,
            routing_method_type=self.routing_method_type,
            do_finalize=True,
            activation_type=activation_to_flashinfer_int(activation),
        )[0]