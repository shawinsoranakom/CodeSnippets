def forward(
            self,
            hidden_states,
            key_value_states=None,
            past_key_value=None,
            attention_mask=None,
            layer_head_mask=None,
            output_attentions=False,
    ):

        is_cross_attention = key_value_states is not None

        bsz, tgt_len, _ = hidden_states.shape
        query_states = self.q_proj(hidden_states) * self.scaling
        if (
                is_cross_attention
                and past_key_value is not None
                and past_key_value[0].shape[2] == key_value_states.shape[1]
        ):
            key_states = past_key_value[0]
            value_states = past_key_value[1]
        elif is_cross_attention:
            key_states = self._shape(self.k_proj(key_value_states), -1, bsz)
            value_states = self._shape(self.v_proj(key_value_states), -1, bsz)
        elif past_key_value is not None:
            key_states = self._shape(self.k_proj(hidden_states), -1, bsz)
            value_states = self._shape(self.v_proj(hidden_states), -1, bsz)
            key_states = torch.concat([past_key_value[0], key_states], dim=2)
            value_states = torch.concat([past_key_value[1], value_states], dim=2)
        else:
            key_states = self._shape(self.k_proj(hidden_states), -1, bsz)
            value_states = self._shape(self.v_proj(hidden_states), -1, bsz)

        if self.is_decoder:
            past_key_value = (key_states, value_states)

        proj_shape = (bsz * self.num_heads, -1, self.head_dim)
        query_states = self._shape(query_states, tgt_len, bsz).reshape(proj_shape)
        key_states = key_states.reshape(proj_shape)
        value_states = value_states.reshape(proj_shape)

        src_len = key_states.shape[1]
        attn_weights = torch.bmm(query_states, key_states.permute([0, 2, 1]))

        if attention_mask is not None:
            attn_weights = (
                    attn_weights.reshape([bsz, self.num_heads, tgt_len, src_len])
                    + attention_mask
            )
            attn_weights = attn_weights.reshape(
                [bsz * self.num_heads, tgt_len, src_len]
            )

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)
        if layer_head_mask is not None:
            if tuple(layer_head_mask.shape) != (self.num_heads,):
                raise ValueError(
                    f"Head mask for a single layer should be of shape {(self.num_heads,)}, but is"
                    f" {layer_head_mask.shape}"
                )
            attn_weights = layer_head_mask.reshape(
                [1, -1, 1, 1]
            ) * attn_weights.reshape([bsz, self.num_heads, tgt_len, src_len])
            attn_weights = attn_weights.reshape(
                [bsz * self.num_heads, tgt_len, src_len]
            )

        if output_attentions:
            attn_weights_reshaped = attn_weights.reshape(
                [bsz, self.num_heads, tgt_len, src_len]
            )
            attn_weights = attn_weights_reshaped.reshape(
                [bsz * self.num_heads, tgt_len, src_len]
            )
        else:
            attn_weights_reshaped = None
        attn_probs = nn.functional.dropout(
            attn_weights, p=self.dropout, training=self.training
        )
        attn_output = torch.bmm(attn_probs, value_states)

        attn_output = attn_output.reshape([bsz, self.num_heads, tgt_len, self.head_dim])
        attn_output = attn_output.permute([0, 2, 1, 3])

        attn_output = attn_output.reshape([bsz, tgt_len, self.embed_dim])
        attn_output = self.out_proj(attn_output)
        return attn_output, attn_weights_reshaped, past_key_value