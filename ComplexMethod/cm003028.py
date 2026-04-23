def forward(
        self,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool = False,
        **kwargs,
    ) -> tuple[torch.Tensor, torch.Tensor | None, tuple[torch.Tensor] | None]:
        """Input shape: Batch x Time x Channel"""

        is_cross_attention = encoder_hidden_states is not None
        batch_size, seq_length = hidden_states.shape[:2]

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
            key_states = self.k_proj(current_states)
            value_states = self.v_proj(current_states)
            key_states = key_states.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
            value_states = value_states.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        query_states = self.q_proj(hidden_states)
        query_states = query_states.reshape(batch_size, seq_length, self.num_heads, self.head_dim).transpose(1, 2)
        query_states = query_states * self.scaling
        attention_scores = torch.matmul(query_states, key_states.transpose(-1, -2))

        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask

        # (batch_size, n_heads, seq_length, key_length)
        attn_weights = nn.functional.softmax(attention_scores.float(), dim=-1).type_as(attention_scores)
        attn_weights = nn.functional.dropout(attn_weights, p=self.dropout, training=self.training)

        #  attn_output = torch.bmm(attn_probs, value_states) ?
        context_states = torch.matmul(attn_weights, value_states)
        # attn_output = attn_output.view(bsz, self.num_heads, tgt_len, self.head_dim) ?
        context_states = context_states.permute(0, 2, 1, 3).contiguous().view(batch_size, seq_length, -1)
        attn_output = self.out_proj(context_states)

        return attn_output, attn_weights