def forward(
        self,
        hidden_states: torch.Tensor,
        layer_past: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        use_cache: bool | None = False,
        output_attentions: bool | None = False,
        **kwargs,
    ) -> tuple:
        is_cross_attention = encoder_hidden_states is not None
        bsz, seq_len, _ = hidden_states.shape

        if layer_past is not None:
            if isinstance(layer_past, EncoderDecoderCache):
                is_updated = layer_past.is_updated.get(self.layer_idx)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = layer_past.cross_attention_cache
                else:
                    curr_past_key_values = layer_past.self_attention_cache
            else:
                curr_past_key_values = layer_past

        current_states = encoder_hidden_states if is_cross_attention else hidden_states
        if is_cross_attention:
            if not hasattr(self, "q_attn"):
                raise ValueError(
                    "If class is used as cross attention, the weights `q_attn` have to be defined. "
                    "Please make sure to instantiate class with `ImageGPTAttention(..., is_cross_attention=True)`."
                )

            if layer_past is not None and is_updated:
                # reuse k,v, cross_attentions, and compute only q
                query = self.q_attn(hidden_states)
                key = curr_past_key_values.layers[self.layer_idx].keys
                value = curr_past_key_values.layers[self.layer_idx].values
            else:
                query = self.q_attn(hidden_states)
                key, value = self.c_attn(current_states).split(self.split_size, dim=2)
                key = key.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)
                value = value.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)
        else:
            query, key, value = self.c_attn(current_states).split(self.split_size, dim=2)
            key = key.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)
            value = value.view(bsz, -1, self.num_heads, self.head_dim).transpose(1, 2)

        if layer_past is not None:
            # save all key/value_states to cache to be re-used for fast auto-regressive generation
            key, value = curr_past_key_values.update(key, value, self.layer_idx)
            # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
            if is_cross_attention:
                layer_past.is_updated[self.layer_idx] = True

        query = query.view(bsz, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        if self.reorder_and_upcast_attn:
            attn_output, attn_weights = self._upcast_and_reordered_attn(query, key, value, attention_mask)
        else:
            attn_output, attn_weights = self._attn(query, key, value, attention_mask)

        attn_output = self._merge_heads(attn_output, self.num_heads, self.head_dim)
        attn_output = self.c_proj(attn_output)
        attn_output = self.resid_dropout(attn_output)

        return attn_output, attn_weights