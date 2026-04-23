def forward(self, hidden_states: torch.Tensor, debug: bool = False) -> torch.Tensor:
        batch_size, sequence_length, hidden_dim = hidden_states.shape
        num_tokens = batch_size * sequence_length
        total_tokens = num_tokens * self.top_k

        hidden_states = hidden_states.view(-1, hidden_dim)

        router_logits, routing_weights, selected_experts = self.run_router(
            hidden_states
        )
        # Pre-processing
        # 1. Compute tokens per expert and indices for gathering tokes from token order to expert order
        # NOTE: these are auxiliary data structs which don't need to be recorded in autograd graph
        token_counts_by_expert, gather_indices = (
            self.get_token_counts_and_gather_indices(selected_experts)
        )

        # 2. permute_x -> permutation will be fused in prologue of first grouped gemm
        if not self.permute_x:
            hidden_states = permute(hidden_states, gather_indices, self.top_k)
            assert hidden_states.shape == (total_tokens, hidden_dim)

        # Start expert computation
        first_gemm = grouped_gemm(
            X = hidden_states,
            W = self.gate_up_proj,
            m_sizes = token_counts_by_expert,
            gather_indices = gather_indices,
            topk = self.top_k,
            permute_x = self.permute_x,
            permute_y = False,  # output of first grouped gemm should never be permuted
            autotune = self.autotune,
            kernel_config_fwd = self.kernel_config_fwd,
            kernel_config_bwd_dW = self.kernel_config_bwd_dW,
            kernel_config_bwd_dX = self.kernel_config_bwd_dX,
            is_first_gemm = True,
        )
        assert first_gemm.shape == (total_tokens, 2 * self.moe_intermediate_size)
        intermediate = self.act_and_mul(first_gemm)
        assert intermediate.shape == (total_tokens, self.moe_intermediate_size)
        second_gemm = grouped_gemm(
            X = intermediate,
            W = self.down_proj,
            m_sizes = token_counts_by_expert,
            gather_indices = gather_indices,
            topk = self.top_k,
            permute_x = False,
            permute_y = self.permute_y,
            autotune = self.autotune,
            kernel_config_fwd = self.kernel_config_fwd,
            kernel_config_bwd_dW = self.kernel_config_bwd_dW,
            kernel_config_bwd_dX = self.kernel_config_bwd_dX,
            is_first_gemm = False,
        )
        assert second_gemm.shape == (total_tokens, hidden_dim)

        # Post-processing
        # 1. Unpermute from expert order to token order
        if not self.permute_y:
            hidden_states_unpermute = unpermute(second_gemm, gather_indices)
            assert hidden_states_unpermute.shape == (total_tokens, hidden_dim)
        else:
            hidden_states_unpermute = second_gemm

        # 2. Merge topk weights
        hidden_states = (
            hidden_states_unpermute.view(num_tokens, self.top_k, hidden_dim)
            * routing_weights[..., None]
        )
        hidden_states = hidden_states.sum(dim = 1)
        assert hidden_states.shape == (num_tokens, hidden_dim)

        hidden_states = hidden_states.view(batch_size, sequence_length, hidden_dim)
        return GroupedGEMMResult(
            token_counts_by_expert = token_counts_by_expert,
            gather_indices = gather_indices,
            topk_weights = routing_weights,
            first_gemm = first_gemm,
            intermediate = intermediate,
            second_gemm = second_gemm,
            hidden_states_unpermute = hidden_states_unpermute,
            hidden_states = hidden_states,
        ), router_logits