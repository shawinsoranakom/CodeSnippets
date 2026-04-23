def forward(
        self,
        hidden_states: torch.Tensor,
        key_value_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool = False,
        # TODO: we need a refactor so that the different attention modules can get their specific kwargs
        # ATM, we have mixed things encoder, decoder, and encoder-decoder attn
        **kwargs: Unpack[FlashAttentionKwargs],
    ) -> tuple[torch.Tensor, torch.Tensor | None, tuple[torch.Tensor] | None]:
        """Input shape: Batch x Time x Channel"""

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = key_value_states is not None

        input_shape = hidden_states.shape[:-1]
        hidden_shape = (*input_shape, -1, self.head_dim)

        # Scaling is susceptible to floating point arithmetics' inprecisions
        # which can lead to different results (this is dependent from model
        # to model, e.g. audioflamingo3 is one such case). We therefore keep the
        # original order of scaling to follow the original implementation
        # and enforce no scaling (1.0) in the attention call below.
        query_states = (self.q_proj(hidden_states) * self.scaling).view(hidden_shape).transpose(1, 2).contiguous()

        # Check is encoder-decoder model is being used. Otherwise we'll get `DynamicCache`
        if past_key_values is not None and isinstance(past_key_values, EncoderDecoderCache):
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
            # reuse k,v, cross_attentions
            key_states = past_key_values.layers[self.layer_idx].keys
            value_states = past_key_values.layers[self.layer_idx].values
        else:
            # Use the query's batch dimension for kv view so that a different-batch
            # encoder output (e.g. in tests) gets absorbed into the sequence axis,
            # preserving backward-compatible behaviour.
            kv_shape = (input_shape[0], -1, self.num_heads, self.head_dim)
            key_states = self.k_proj(current_states).view(kv_shape).transpose(1, 2).contiguous()
            value_states = self.v_proj(current_states).view(kv_shape).transpose(1, 2).contiguous()
            if past_key_values is not None:
                key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)

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
            scaling=1.0,
            output_attentions=output_attentions,
            **kwargs,
        )

        attn_output = attn_output.reshape(*input_shape, -1).contiguous()
        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights