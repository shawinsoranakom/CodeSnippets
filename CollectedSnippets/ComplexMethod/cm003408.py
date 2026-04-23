def forward(
        self,
        hidden_states: torch.Tensor,
        cache_params: OlmoHybridDynamicCache | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> torch.Tensor:
        # Requires LEFT padding to work correctly
        hidden_states = apply_mask_to_padding_states(hidden_states, attention_mask)

        batch_size, seq_len, _ = hidden_states.shape

        use_cache = cache_params is not None
        use_precomputed = use_cache and cache_params.has_previous_state() and seq_len == 1

        conv_state_q = cache_params.conv_states_q[self.layer_idx] if cache_params else None
        conv_state_k = cache_params.conv_states_k[self.layer_idx] if cache_params else None
        conv_state_v = cache_params.conv_states_v[self.layer_idx] if cache_params else None
        recurrent_state = cache_params.recurrent_states[self.layer_idx] if cache_params else None

        q = self.q_proj(hidden_states)
        k = self.k_proj(hidden_states)
        v = self.v_proj(hidden_states)

        q, new_conv_state_q = self.q_conv1d(
            q, cache=conv_state_q, use_precomputed=use_precomputed, output_final_state=use_cache
        )
        k, new_conv_state_k = self.k_conv1d(
            k, cache=conv_state_k, use_precomputed=use_precomputed, output_final_state=use_cache
        )
        v, new_conv_state_v = self.v_conv1d(
            v, cache=conv_state_v, use_precomputed=use_precomputed, output_final_state=use_cache
        )

        if cache_params is not None:
            cache_params.conv_states_q[self.layer_idx] = new_conv_state_q
            cache_params.conv_states_k[self.layer_idx] = new_conv_state_k
            cache_params.conv_states_v[self.layer_idx] = new_conv_state_v

        q = q.view(batch_size, seq_len, -1, self.head_k_dim)
        k = k.view(batch_size, seq_len, -1, self.head_k_dim)
        v = v.view(batch_size, seq_len, -1, self.head_v_dim)

        if self.num_v_heads > self.num_k_heads:
            expand_ratio = self.num_v_heads // self.num_k_heads
            q = q.repeat_interleave(expand_ratio, dim=2)
            k = k.repeat_interleave(expand_ratio, dim=2)

        beta = self.b_proj(hidden_states).sigmoid()
        if self.allow_neg_eigval:
            beta = beta * 2.0

        g = -self.A_log.float().exp() * F.softplus(self.a_proj(hidden_states).float() + self.dt_bias)

        if use_precomputed:
            output, new_recurrent_state = self.recurrent_gated_delta_rule(
                q,
                k,
                v,
                g=g,
                beta=beta,
                initial_state=recurrent_state,
                output_final_state=use_cache,
                use_qk_l2norm_in_kernel=True,
            )
        else:
            output, new_recurrent_state = self.chunk_gated_delta_rule(
                q,
                k,
                v,
                g=g,
                beta=beta,
                initial_state=recurrent_state,
                output_final_state=use_cache,
                use_qk_l2norm_in_kernel=True,
            )

        if cache_params is not None:
            cache_params.recurrent_states[self.layer_idx] = new_recurrent_state

        gate = self.g_proj(hidden_states)
        output = output.reshape(-1, self.head_v_dim)
        gate = gate.reshape(-1, self.head_v_dim)
        output = self.o_norm(output, gate)
        output = output.reshape(batch_size, seq_len, -1)

        output = self.o_proj(output)

        return output