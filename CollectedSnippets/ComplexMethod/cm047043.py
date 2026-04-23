def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        """ """
        batch_size, sequence_length, hidden_dim = hidden_states.shape
        num_tokens = batch_size * sequence_length
        total_tokens = num_tokens * self.top_k
        hidden_states = hidden_states.view(-1, hidden_dim)

        if self.overlap_router_shared:
            # Marker for all prior ops on default stream
            self.default_event.record()

        router_logits, routing_weights, selected_experts = self.run_router(
            hidden_states
        )
        assert routing_weights.shape == (
            num_tokens,
            self.top_k,
        ), f"{routing_weights.shape} != {(num_tokens, self.top_k)}"

        if self.overlap_router_shared:
            with torch.cuda.stream(self.shared_expert_stream):
                # Ensure prior kernels on default stream complete
                self.default_event.wait()

                shared_expert_out = self.shared_expert(hidden_states)
                # Ensure hidden states remains valid on this stream
                hidden_states.record_stream(self.shared_expert_stream)

                self.shared_expert_end_event.record()

            # Ensure shared expert still valid on default stream
            shared_expert_out.record_stream(torch.cuda.current_stream())
            self.shared_expert_end_event.wait()
        else:
            shared_expert_out = self.shared_expert(hidden_states)

        hidden_states = (
            hidden_states.view(num_tokens, self.top_k, hidden_dim)
            * routing_weights[..., None]
        )

        if self.top_k > 1:
            hidden_states = hidden_states.sum(dim = 1)
        hidden_states_after_weight_merge = hidden_states.view(-1, hidden_dim)

        # 1. Compute tokens per expert and indices for gathering tokes from token order to expert order
        # NOTE: these are auxiliary data structs which don't need to be recorded in autograd graph
        token_counts_by_expert, gather_indices = (
            self.get_token_counts_and_gather_indices(selected_experts)
        )

        # 2. Permute tokens from token order to expert order
        hidden_states = permute(
            hidden_states_after_weight_merge, gather_indices, self.top_k
        )
        assert hidden_states.shape == (total_tokens, hidden_dim)

        # Start expert computation
        first_gemm = torch_grouped_gemm(
            X = hidden_states, W = self.experts.gate_up_proj, m_sizes = token_counts_by_expert
        )
        assert first_gemm.shape == (total_tokens, 2 * self.experts.expert_dim)

        intermediate = self.act_and_mul(first_gemm)
        assert intermediate.shape == (total_tokens, self.experts.expert_dim)

        # See comment above
        second_gemm = torch_grouped_gemm(
            X = intermediate, W = self.experts.down_proj, m_sizes = token_counts_by_expert
        )
        assert second_gemm.shape == (total_tokens, hidden_dim)

        # Post-processing
        hidden_states_unpermute = unpermute(second_gemm, gather_indices)
        assert hidden_states_unpermute.shape == (total_tokens, hidden_dim)
        # grouped_gemm_out = hidden_states.view(batch_size, sequence_length, hidden_dim)

        final_out = hidden_states_unpermute + shared_expert_out

        result = (
            Llama4MoeResult(
                token_counts_by_expert = token_counts_by_expert,
                gather_indices = gather_indices,
                topk_weights = routing_weights,
                hidden_states_after_weight_merge = hidden_states_after_weight_merge,
                first_gemm = first_gemm,
                intermediate = intermediate,
                second_gemm = second_gemm,
                hidden_states_unpermute = hidden_states_unpermute,
                shared_expert_out = shared_expert_out,
                final_out = final_out,
                router_logits = router_logits,
            )
            if self.debug
            else (final_out, routing_weights)
        )

        return result