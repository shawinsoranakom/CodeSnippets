def forward(
        self,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        **kwargs,
    ):
        batch_size, seq_length = hidden_states.shape[:2]
        past_seen_tokens = past_key_values.get_seq_length(self.layer_idx) if past_key_values is not None else 0
        # We clone here for StaticCache, as we get the value before updating it, but use it after and it's the same ref
        past_seen_tokens = past_seen_tokens.clone() if isinstance(past_seen_tokens, torch.Tensor) else past_seen_tokens

        # if encoder_hidden_states are provided this layer is used as a cross-attention layer for the decoder
        is_cross_attention = encoder_hidden_states is not None

        query_states = self.q(hidden_states)
        query_states = query_states.view(batch_size, -1, self.n_heads, self.key_value_proj_dim).transpose(1, 2)

        # Check is encoder-decoder model is being used. Otherwise we'll get `DynamicCache`
        is_updated = False
        if past_key_values is not None and isinstance(past_key_values, EncoderDecoderCache):
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
            key_states = self.k(current_states)
            value_states = self.v(current_states)
            key_states = key_states.view(batch_size, -1, self.n_heads, self.key_value_proj_dim).transpose(1, 2)
            value_states = value_states.view(batch_size, -1, self.n_heads, self.key_value_proj_dim).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        # compute scores, equivalent of torch.einsum("bnqd,bnkd->bnqk", query_states, key_states), compatible with onnx op>9
        scores = torch.matmul(query_states, key_states.transpose(3, 2))

        key_length = key_states.shape[-2]
        if not self.has_relative_attention_bias:
            position_bias = torch.zeros(
                (1, self.n_heads, seq_length, key_length), device=scores.device, dtype=scores.dtype
            )
        else:
            position_bias = self.compute_bias(
                seq_length, key_length, device=scores.device, past_seen_tokens=past_seen_tokens
            )

        if attention_mask is not None:
            position_bias = position_bias + attention_mask

        position_bias_masked = position_bias
        scores += position_bias_masked

        # (batch_size, n_heads, seq_length, key_length)
        attn_weights = nn.functional.softmax(scores.float(), dim=-1).type_as(scores)
        attn_weights = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)

        attn_output = torch.matmul(attn_weights, value_states)

        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_length, -1)

        attn_output = self.o(attn_output)
        return attn_output, attn_weights