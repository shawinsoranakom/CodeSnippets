def forward(
        self,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor | None, Cache | None]:
        """Input shape: Batch x Time x Channel"""

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = encoder_hidden_states is not None
        input_shape = hidden_states.shape[:-1]

        hidden_shape = (*input_shape, -1, self.head_dim)
        query_states = self.q_proj(hidden_states)
        query_states = query_states.view(hidden_shape).transpose(1, 2)

        is_updated = False
        if past_key_values is not None:
            if isinstance(past_key_values, EncoderDecoderCache):
                is_updated = past_key_values.is_updated.get(self.layer_idx)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = past_key_values.cross_attention_cache
                else:
                    curr_past_key_values = past_key_values.self_attention_cache
            else:
                curr_past_key_values = past_key_values

        current_states = encoder_hidden_states if is_cross_attention else hidden_states
        if is_cross_attention and past_key_values is not None and is_updated:
            # reuse k,v, cross_attentions
            key_states = curr_past_key_values.layers[self.layer_idx].keys
            value_states = curr_past_key_values.layers[self.layer_idx].values
        else:
            kv_shape = (*current_states.shape[:-1], -1, self.head_dim)
            key_states = self.k_proj(current_states).view(kv_shape).transpose(1, 2)
            value_states = self.v_proj(current_states).view(kv_shape).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        attention_interface: Callable = ALL_ATTENTION_FUNCTIONS.get_interface(
            self.config._attn_implementation, eager_attention_forward
        )

        attn_output, attn_weights = attention_interface(
            self,
            query_states,
            key_states,
            value_states,
            attention_mask,
            dropout=0.0 if not self.training else self.dropout,
            scaling=self.scaling,
            **kwargs,
        )

        attn_output = attn_output.reshape(*input_shape, -1).contiguous()
        if self.inner_attn_ln is not None:
            attn_output = self.inner_attn_ln(attn_output)

        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights