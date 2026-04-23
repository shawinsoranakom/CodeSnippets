def forward(
        self,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor] | None = None,
        attention_mask: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        key_value_states: torch.Tensor | None = None,
        **kwargs: Unpack[FlashAttentionKwargs],
    ) -> tuple[torch.Tensor, torch.Tensor | None, tuple[torch.Tensor] | None]:
        bsz, q_len = hidden_states.shape[:-1]

        query_states = (
            self.q_proj(hidden_states).view(bsz, q_len, self.config.num_key_value_heads, self.head_dim).transpose(1, 2)
        )

        is_cross_attention = key_value_states is not None
        if past_key_values is not None:
            is_updated = past_key_values.is_updated.get(self.layer_idx)
            if is_cross_attention:
                # after the first generated id, we can subsequently re-use all key/value_states from cache
                past_key_values.is_updated[self.layer_idx] = True
                past_key_values = past_key_values.cross_attention_cache
            else:
                past_key_values = past_key_values.self_attention_cache

        # use key_value_states if cross attention
        current_states = key_value_states if key_value_states is not None else hidden_states
        if is_cross_attention and past_key_values and is_updated:
            key_states = past_key_values.layers[self.layer_idx].keys
            value_states = past_key_values.layers[self.layer_idx].values
        else:
            key_states = (
                self.k_proj(current_states)
                .view(bsz, -1, self.config.num_key_value_heads, self.head_dim)
                .transpose(1, 2)
            )
            value_states = (
                self.v_proj(current_states)
                .view(bsz, -1, self.config.num_key_value_heads, self.head_dim)
                .transpose(1, 2)
            )
            if is_cross_attention and past_key_values is not None:
                key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)

        if not is_cross_attention:
            cos, sin = position_embeddings
            query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

            if past_key_values is not None:
                key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)

        attention_interface: Callable = ALL_ATTENTION_FUNCTIONS.get_interface(
            self.config._attn_implementation, eager_attention_forward
        )

        is_causal = self.is_causal and attention_mask is None and q_len > 1

        if self.head_dim_padding > 0:
            query_states = torch.nn.functional.pad(query_states, (0, self.head_dim_padding))
            key_states = torch.nn.functional.pad(key_states, (0, self.head_dim_padding))
            value_states = torch.nn.functional.pad(value_states, (0, self.head_dim_padding))

        attn_output, attn_weights = attention_interface(
            self,
            query_states,
            key_states,
            value_states,
            attention_mask,
            dropout=0.0 if not self.training else self.attention_dropout,
            scaling=self.scaling,
            is_causal=is_causal,
            **kwargs,
        )

        if self.head_dim_padding > 0:
            attn_output = attn_output[..., : -self.head_dim_padding]

        attn_output = attn_output.reshape(bsz, q_len, -1).contiguous()
        attn_output = self.o_proj(attn_output)
        return attn_output, attn_weights