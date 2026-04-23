def _forward(
        self,
        q_proj_states: torch.Tensor,
        k_proj_states: torch.Tensor,
        v_proj_states: torch.Tensor,
        g1: torch.Tensor,
        beta: torch.Tensor,
        core_attn_out: torch.Tensor,
    ) -> None:
        forward_context = get_forward_context()
        attn_metadata_raw = forward_context.attn_metadata

        if attn_metadata_raw is None:
            #     # V1 profile run
            return

        assert isinstance(attn_metadata_raw, dict)
        attn_metadata_narrowed = attn_metadata_raw[self.prefix]
        assert isinstance(attn_metadata_narrowed, GDNAttentionMetadata)
        has_initial_state = attn_metadata_narrowed.has_initial_state
        non_spec_query_start_loc = attn_metadata_narrowed.non_spec_query_start_loc
        non_spec_state_indices_tensor = (
            attn_metadata_narrowed.non_spec_state_indices_tensor
        )  # noqa: E501
        num_actual_tokens = attn_metadata_narrowed.num_actual_tokens
        constant_caches = self.kv_cache

        q_proj_states = q_proj_states[:num_actual_tokens]
        k_proj_states = k_proj_states[:num_actual_tokens]
        v_proj_states = v_proj_states[:num_actual_tokens]
        g1 = g1[:num_actual_tokens]
        beta = beta[:num_actual_tokens]

        (conv_state_q, conv_state_k, conv_state_v, recurrent_state) = constant_caches
        # conv_state must be (..., dim, width-1) for the conv kernels.
        # DS layout stores it that way directly; SD layout needs a transpose.
        if not is_conv_state_dim_first():
            conv_state_q = conv_state_q.transpose(-1, -2)
            conv_state_k = conv_state_k.transpose(-1, -2)
            conv_state_v = conv_state_v.transpose(-1, -2)

        q_conv_weights = self.q_conv1d.weight.view(
            self.q_conv1d.weight.size(0), self.q_conv1d.weight.size(2)
        )
        k_conv_weights = self.k_conv1d.weight.view(
            self.k_conv1d.weight.size(0), self.k_conv1d.weight.size(2)
        )
        v_conv_weights = self.v_conv1d.weight.view(
            self.v_conv1d.weight.size(0), self.v_conv1d.weight.size(2)
        )
        if attn_metadata_narrowed.num_prefills > 0:
            q_proj_states = q_proj_states.transpose(0, 1)
            k_proj_states = k_proj_states.transpose(0, 1)
            v_proj_states = v_proj_states.transpose(0, 1)
            q = causal_conv1d_fn(
                q_proj_states,
                q_conv_weights,
                self.q_conv1d.bias,
                activation="silu",
                conv_states=conv_state_q,
                has_initial_state=has_initial_state,
                cache_indices=non_spec_state_indices_tensor,
                query_start_loc=non_spec_query_start_loc,
                metadata=attn_metadata_narrowed,
            ).transpose(0, 1)
            k = causal_conv1d_fn(
                k_proj_states,
                k_conv_weights,
                self.k_conv1d.bias,
                activation="silu",
                conv_states=conv_state_k,
                has_initial_state=has_initial_state,
                cache_indices=non_spec_state_indices_tensor,
                query_start_loc=non_spec_query_start_loc,
                metadata=attn_metadata_narrowed,
            ).transpose(0, 1)
            v = causal_conv1d_fn(
                v_proj_states,
                v_conv_weights,
                self.v_conv1d.bias,
                activation="silu",
                conv_states=conv_state_v,
                has_initial_state=has_initial_state,
                cache_indices=non_spec_state_indices_tensor,
                query_start_loc=non_spec_query_start_loc,
                metadata=attn_metadata_narrowed,
            ).transpose(0, 1)
        else:
            assert non_spec_state_indices_tensor is not None
            decode_conv_indices = non_spec_state_indices_tensor[
                : attn_metadata_narrowed.num_actual_tokens
            ]
            q = causal_conv1d_update(
                q_proj_states,
                conv_state_q,
                q_conv_weights,
                self.q_conv1d.bias,
                activation="silu",
                conv_state_indices=decode_conv_indices,
                validate_data=True,
            )
            k = causal_conv1d_update(
                k_proj_states,
                conv_state_k,
                k_conv_weights,
                self.k_conv1d.bias,
                activation="silu",
                conv_state_indices=decode_conv_indices,
                validate_data=True,
            )
            v = causal_conv1d_update(
                v_proj_states,
                conv_state_v,
                v_conv_weights,
                self.v_conv1d.bias,
                activation="silu",
                conv_state_indices=decode_conv_indices,
                validate_data=True,
            )

        q, k, v = map(
            lambda x: rearrange(x, "n (h d) -> 1 n h d", d=self.head_dim), (q, k, v)
        )

        if attn_metadata_narrowed.num_prefills > 0:
            assert non_spec_state_indices_tensor is not None
            assert has_initial_state is not None
            zero_idx = non_spec_state_indices_tensor[~has_initial_state]
            recurrent_state[zero_idx] = 0
            initial_state = recurrent_state[non_spec_state_indices_tensor].contiguous()
            (
                core_attn_out_non_spec,
                last_recurrent_state,
            ) = chunk_kda(
                q=q,
                k=k,
                v=v,
                g=g1,
                beta=beta,
                initial_state=initial_state,
                output_final_state=True,
                use_qk_l2norm_in_kernel=True,
                cu_seqlens=non_spec_query_start_loc,
            )
            # Init cache
            recurrent_state[non_spec_state_indices_tensor] = last_recurrent_state
        else:
            assert non_spec_query_start_loc is not None
            (
                core_attn_out_non_spec,
                last_recurrent_state,
            ) = fused_recurrent_kda(
                q=q,
                k=k,
                v=v,
                g=g1,
                beta=beta,
                initial_state=recurrent_state,
                use_qk_l2norm_in_kernel=True,
                cu_seqlens=non_spec_query_start_loc[
                    : attn_metadata_narrowed.num_decodes + 1
                ],
                ssm_state_indices=non_spec_state_indices_tensor,
            )
        core_attn_out[0, :num_actual_tokens] = core_attn_out_non_spec[
            0, :num_actual_tokens
        ]