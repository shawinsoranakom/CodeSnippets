def forward(
        self,
        hidden_states,
        attention_mask=None,
        encoder_hidden_states=None,
        past_key_values=None,
        output_attentions=False,
        **kwargs,
    ):
        input_shape = hidden_states.shape[:-1]
        hidden_shape = (*input_shape, -1, self.attention_head_size)
        query_layer = self.query(hidden_states).view(hidden_shape).transpose(1, 2)

        is_updated = False
        is_cross_attention = encoder_hidden_states is not None
        if past_key_values is not None:
            if isinstance(past_key_values, EncoderDecoderCache):
                is_updated = past_key_values.is_updated.get(self.layer_idx)
                if is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_layer from cache
                    curr_past_key_values = past_key_values.cross_attention_cache
                else:
                    curr_past_key_values = past_key_values.self_attention_cache
            else:
                curr_past_key_values = past_key_values

        current_states = encoder_hidden_states if is_cross_attention else hidden_states
        if is_cross_attention and past_key_values is not None and is_updated:
            # reuse k,v, cross_attentions
            key_layer = curr_past_key_values.layers[self.layer_idx].keys
            value_layer = curr_past_key_values.layers[self.layer_idx].values
        else:
            key_layer = self.key(current_states).view(hidden_shape).transpose(1, 2)
            value_layer = self.value(current_states).view(hidden_shape).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_layer to cache to be re-used for fast auto-regressive generation
                key_layer, value_layer = curr_past_key_values.update(key_layer, value_layer, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if is_cross_attention and isinstance(past_key_values, EncoderDecoderCache):
                    past_key_values.is_updated[self.layer_idx] = True

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        if attention_mask is not None:
            # Apply the attention mask is (precomputed for all layers in TapasModel forward() function)
            attention_scores = attention_scores + attention_mask

        # Normalize the attention scores to probabilities.
        attention_probs = nn.functional.softmax(attention_scores, dim=-1)

        # This is actually dropping out entire tokens to attend to, which might
        # seem a bit unusual, but is taken from the original Transformer paper.
        attention_probs = self.dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)

        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)

        outputs = (context_layer, attention_probs) if output_attentions else (context_layer,)
        if self.is_decoder:
            outputs = outputs + (past_key_values,)
        return outputs