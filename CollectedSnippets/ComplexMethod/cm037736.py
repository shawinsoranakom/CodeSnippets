def forward_cuda(
        self,
        hidden_states: torch.Tensor,
        output: torch.Tensor,
    ):
        forward_context = get_forward_context()
        # ShortConvAttentionMetadata contains metadata necessary for the
        # short_conv triton kernels to operate in continuous batching and in
        # chunked prefill modes; they are computed at top-level model forward
        # since they stay the same and reused for all mamba layers in the same
        # iteration.
        attn_metadata_raw = forward_context.attn_metadata
        attn_metadata: AttentionMetadata | None = None
        if attn_metadata_raw is not None:
            assert isinstance(attn_metadata_raw, dict)
            attn_metadata = attn_metadata_raw[self.prefix]
            assert isinstance(attn_metadata, ShortConvAttentionMetadata)
            conv_state = (
                self.kv_cache[0]
                if is_conv_state_dim_first()
                else self.kv_cache[0].transpose(-1, -2)
            )
            state_indices_tensor_p = attn_metadata.state_indices_tensor_p
            state_indices_tensor_d = attn_metadata.state_indices_tensor_d
            has_initial_states_p = attn_metadata.has_initial_states_p
            query_start_loc_p = attn_metadata.query_start_loc_p

        BCx, _ = self.in_proj(hidden_states)

        B, C, x = BCx.chunk(3, dim=-1)

        conv_weights = self.conv.weight.view(
            self.conv.weight.size(0), self.conv.weight.size(2)
        )

        if attn_metadata is None:
            # V1 profile run
            Bx = (B * x).contiguous()
            hidden_states = C * Bx
            contextualized_states, _ = self.out_proj(hidden_states)
            return contextualized_states

        num_prefills = attn_metadata.num_prefills  # request count
        num_decodes = attn_metadata.num_decode_tokens  # token count (=request)
        num_prefill_tokens = attn_metadata.num_prefill_tokens  # token count
        has_prefill = num_prefills > 0
        has_decode = num_decodes > 0
        num_actual_tokens = num_decodes + num_prefill_tokens

        # NOTE: V1 puts decode before prefill
        # Separate prefill and decode by splitting varlen input
        # Split along token dimension
        B_d, B_p = torch.split(
            B[:num_actual_tokens],
            [num_decodes, num_prefill_tokens],
            dim=0,
        )
        C_d, C_p = torch.split(
            C[:num_actual_tokens],
            [num_decodes, num_prefill_tokens],
            dim=0,
        )
        x_d, x_p = torch.split(
            x[:num_actual_tokens],
            [num_decodes, num_prefill_tokens],
            dim=0,
        )
        conv_output_list = []

        if has_prefill:
            Bx_p = (B_p * x_p).transpose(0, 1)
            Bx = causal_conv1d_fn(
                Bx_p,
                conv_weights,
                self.conv.bias,
                activation=None,
                conv_states=conv_state,
                has_initial_state=has_initial_states_p,
                cache_indices=state_indices_tensor_p,
                metadata=attn_metadata,
                query_start_loc=query_start_loc_p,
            ).transpose(0, 1)[:num_prefill_tokens]

            y = C_p * Bx
            conv_output_list.append(y)

        if has_decode:
            Bx_d = (B_d * x_d).contiguous()
            Bx = causal_conv1d_update(
                Bx_d,
                conv_state,
                conv_weights,
                self.conv.bias,
                activation=None,
                conv_state_indices=state_indices_tensor_d,
            )
            y = C_d * Bx
            conv_output_list.insert(0, y)

        # Merge prefill and decode outputs before passing to gated MLP
        hidden_states = torch.vstack(conv_output_list)

        # Final linear projection
        output[:num_actual_tokens], _ = self.out_proj(hidden_states)