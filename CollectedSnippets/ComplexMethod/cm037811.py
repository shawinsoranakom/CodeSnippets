def apply(
        self,
        output: torch.Tensor,
        hidden_states: torch.Tensor,
        w1: torch.Tensor,
        w2: torch.Tensor,
        topk_weights: torch.Tensor,
        topk_ids: torch.Tensor,
        activation: MoEActivation,
        global_num_experts: int,
        expert_map: torch.Tensor | None,
        a1q_scale: torch.Tensor | None,
        a2_scale: torch.Tensor | None,
        workspace13: torch.Tensor,
        workspace2: torch.Tensor,
        expert_tokens_meta: mk.ExpertTokensMetadata | None,
        apply_router_weight_on_input: bool,
    ):
        # Use local variable to help mypy narrow the type after None check
        quant_config = self.quant_config
        if quant_config is None:
            quant_config = FUSED_MOE_UNQUANTIZED_CONFIG

        if expert_map is not None:
            topk_ids = expert_map[topk_ids]

        local_num_experts = w1.shape[0]
        if global_num_experts == -1:
            global_num_experts = local_num_experts

        routing_data, gather_indx, scatter_indx = self._make_routing_data(
            topk_ids, topk_weights, local_num_experts
        )

        topk = topk_ids.size(1)

        # type check, uint8 means mxfp4
        assert hidden_states.dtype == torch.bfloat16
        assert (
            quant_config.w1_bias is None or quant_config.w1_bias.dtype == torch.float32
        )
        assert (
            quant_config.w2_bias is None or quant_config.w2_bias.dtype == torch.float32
        )

        # Shape check, only check non-mxfp4
        assert hidden_states.ndim == 2
        assert hidden_states.shape[-1] == w1.shape[-2]
        assert w2.shape[-1] == w1.shape[1]

        batch_dim = 1
        M, K = hidden_states.shape
        E, _, N = w1.shape

        if global_num_experts == -1:
            global_num_experts = E

        # Note that the output tensor might be in workspace13
        intermediate_cache1 = _resize_cache(workspace2, (batch_dim, M * topk, N))
        intermediate_cache3 = _resize_cache(workspace2, (batch_dim, M * topk, K))
        activation_out_dim = self.adjust_N_for_activation(N, activation)
        intermediate_cache2 = _resize_cache(workspace13, (M * topk, activation_out_dim))

        gammas = routing_data.gate_scal if routing_data else None

        matmul_ogs(
            hidden_states,
            w1,
            quant_config.w1_bias,
            routing_data,
            gather_indx=gather_indx,
            precision_config=quant_config.w1_precision,
            gammas=gammas if apply_router_weight_on_input else None,
            fused_activation=None,
            y=intermediate_cache1,
        )

        self.activation(
            activation,
            intermediate_cache2,
            intermediate_cache1.view(-1, N)[gather_indx.dst_indx],
        )

        # matmul_ogs grouped reduction fuse sum across multiple experts:
        # y[dst_indx // n_expts_act, :] += x
        # Need to set n_expts_act to 1 to unfuse moe_sum
        routing_data.n_expts_act = 1

        matmul_ogs(
            intermediate_cache2[gather_indx.src_indx],
            w2,
            quant_config.w2_bias,
            routing_data,
            scatter_indx=scatter_indx,
            precision_config=quant_config.w2_precision,
            gammas=None if apply_router_weight_on_input else gammas,
            y=intermediate_cache3,
        )

        self.moe_sum(intermediate_cache3.view(-1, topk, K), output)