def forward(
        self,
        hidden_states,
        attention_mask=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        past_key_values=None,
        **kwargs: Unpack[TransformersKwargs],
    ):
        input_shape = hidden_states.shape[:-1]
        hidden_shape = (*input_shape, -1, self.attention_head_size)
        query_layer = self.query(hidden_states).view(hidden_shape).transpose(1, 2)

        is_cross_attention = encoder_hidden_states is not None
        current_states = encoder_hidden_states if is_cross_attention else hidden_states
        attention_mask = encoder_attention_mask if is_cross_attention else attention_mask
        if is_cross_attention and past_key_values is not None and past_key_values.get_seq_length(self.layer_idx) > 0:
            # reuse k,v, cross_attentions
            key_layer = past_key_values.layers[self.layer_idx].keys
            value_layer = past_key_values.layers[self.layer_idx].values
        else:
            kv_shape = (*current_states.shape[:-1], -1, self.attention_head_size)
            key_layer = self.key(current_states).view(kv_shape).transpose(1, 2)
            value_layer = self.value(current_states).view(kv_shape).transpose(1, 2)

            if past_key_values is not None:
                # save all key/value_layer to cache to be re-used for fast auto-regressive generation
                key_layer, value_layer = past_key_values.update(
                    key_layer,
                    value_layer,
                    self.layer_idx,
                )

        # Take the dot product between "query" and "key" to get the raw attention scores.
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))

        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        if attention_mask is not None:
            # Apply the attention mask is (precomputed for all layers in BigBirdPegasusModel forward() function)
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

        return context_layer, attention_probs