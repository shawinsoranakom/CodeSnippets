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
    ) -> tuple[torch.Tensor, torch.Tensor | None] | tuple[torch.Tensor, torch.Tensor | None, tuple[torch.Tensor, ...]]:
        input_shape = hidden_states.shape[:-1]

        if layer_past is not None:
            if isinstance(layer_past, EncoderDecoderCache):
                is_updated = layer_past.is_updated.get(self.layer_idx)
                if self.is_cross_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = layer_past.cross_attention_cache
                else:
                    curr_past_key_values = layer_past.self_attention_cache
            else:
                curr_past_key_values = layer_past

        if self.is_cross_attention:
            if not hasattr(self, "q_attn") or not self.is_cross_attention:
                raise ValueError(
                    "If class is used as cross attention, the weights `q_attn` have to be defined. "
                    "Please make sure to instantiate class with `GPTBigCodeAttention(..., is_cross_attention=True)`."
                )
            if layer_past is not None and is_updated:
                # reuse k,v, cross_attentions
                key = curr_past_key_values.layers[self.layer_idx].keys
                value = curr_past_key_values.layers[self.layer_idx].values
            else:
                query = self.q_attn(hidden_states).view(*input_shape, -1, self.head_dim).transpose(1, 2)
                key, value = self.c_attn(encoder_hidden_states).split((self.head_dim, self.head_dim), dim=-1)
        else:
            if self.multi_query:
                query, key, value = (
                    self.c_attn(hidden_states).unsqueeze(1).split((self.embed_dim, self.kv_dim, self.kv_dim), dim=3)
                )
                query = query.view(*input_shape, -1, self.head_dim).transpose(1, 2)
            else:
                query, key, value = (
                    self.c_attn(hidden_states)
                    .view(*hidden_states.shape[:2], self.num_heads, 3 * self.head_dim)
                    .transpose(1, 2)
                    .split(3 * [self.head_dim], dim=3)
                )

        if layer_past is not None:
            # save all key/value_states to cache to be re-used for fast auto-regressive generation
            key, value = curr_past_key_values.update(key, value, self.layer_idx)
            # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
            if self.is_cross_attention:
                layer_past.is_updated[self.layer_idx] = True

        attention_interface: Callable = ALL_ATTENTION_FUNCTIONS.get_interface(
            self.config._attn_implementation, eager_attention_forward
        )

        attn_output, attn_weights = attention_interface(
            self,
            query,
            key,
            value,
            attention_mask,
            dropout=0.0 if not self.training else self.attn_dropout,
            scaling=self.scaling,
            **kwargs,
        )

        attn_output = attn_output.reshape(*input_shape, -1).contiguous()
        attn_output = self.c_proj(attn_output)
        attn_output = self.resid_dropout(attn_output)
        return attn_output, attn_weights