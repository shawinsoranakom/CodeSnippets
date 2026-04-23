def forward(
        self,
        hidden_states,
        key_value_states: Tensor | None = None,
        attention_mask: Tensor | None = None,
        past_key_values: Cache | None = None,
        output_attentions: bool | None = False,
        **kwargs,
    ) -> tuple[Tensor, Tensor | None]:
        batch_size, tgt_len, hidden_size = hidden_states.size()

        # if key_value_states are provided this layer is used as a cross-attention layer
        # for the decoder
        is_cross_attention = key_value_states is not None
        assert list(hidden_states.size()) == [
            batch_size,
            tgt_len,
            hidden_size,
        ], f"Size of hidden states should be {batch_size, tgt_len, hidden_size}, but is {hidden_states.size()}"

        # previous time steps are cached - no need to recompute key and value if they are static
        query_states = self.query_proj(hidden_states) / (self.head_dim**0.5)

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

        current_states = key_value_states if is_cross_attention else hidden_states
        if is_cross_attention and past_key_values is not None and is_updated:
            # reuse k,v, cross_attentions
            key_states = curr_past_key_values.layers[self.layer_idx].keys
            value_states = curr_past_key_values.layers[self.layer_idx].values
        else:
            key_states = self.key_proj(current_states)
            value_states = self.value_proj(current_states)
            key_states = key_states.view(batch_size, -1, self.num_attn_heads, self.head_dim).transpose(1, 2)
            value_states = value_states.view(batch_size, -1, self.num_attn_heads, self.head_dim).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        query_states = query_states.view(batch_size, tgt_len, self.num_attn_heads, self.head_dim).transpose(1, 2)
        src_len = key_states.size(2)

        attn_weights = torch.einsum("bsij,bsjk->bsik", query_states, key_states.transpose(2, 3))
        expected_shape = (batch_size, self.num_attn_heads, tgt_len, src_len)
        if attn_weights.size() != expected_shape:
            raise ValueError(f"Attention weights should have size {expected_shape}, but is {attn_weights.size()}")

        # This is part of a workaround to get around fork/join parallelism not supporting Optional types.
        if attention_mask is not None and attention_mask.dim() == 0:
            attention_mask = None

        expected_shape = (batch_size, self.num_attn_heads, 1, src_len)
        if attention_mask is not None and attention_mask.size() != expected_shape:
            raise ValueError(f"Attention mask should have size {expected_shape}, but is {attention_mask.size()}")
        if attention_mask is not None:  # don't attend to padding symbols
            attn_weights = attn_weights + attention_mask
        if output_attentions:
            attn_weights_reshaped = attn_weights
        else:
            attn_weights_reshaped = None

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)

        attn_probs = nn.functional.dropout(
            attn_weights,
            p=self.attention_dropout,
            training=self.training,
        )
        attn_output = torch.einsum("bsij,bsjk->bsik", attn_probs, value_states)
        expected_shape = (batch_size, self.num_attn_heads, tgt_len, self.head_dim)
        if attn_output.size() != expected_shape:
            raise ValueError(f"`attn_output` should have shape {expected_shape}, but is of shape {attn_output.size()}")

        attn_output = attn_output.transpose(1, 2).reshape(batch_size, tgt_len, hidden_size)
        attn_output = self.out_proj(attn_output)

        attn_output = nn.functional.dropout(attn_output, p=self.dropout, training=self.training)
        return attn_output, attn_weights_reshaped