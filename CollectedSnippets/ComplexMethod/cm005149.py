def forward(
        self,
        query,
        key: Tensor | None,
        key_padding_mask: Tensor | None = None,
        layer_state: Cache | None = None,
        attn_mask: Tensor | None = None,
        output_attentions: bool | None = False,
        **kwargs,
    ) -> tuple[Tensor, Tensor | None]:
        """Input shape: Time(SeqLen) x Batch x Channel"""
        tgt_len, bsz, embed_dim = query.size()
        assert embed_dim == self.embed_dim
        assert list(query.size()) == [tgt_len, bsz, embed_dim]

        if layer_state is not None:
            if isinstance(layer_state, EncoderDecoderCache):
                is_updated = layer_state.is_updated.get(self.layer_idx)
                if self.encoder_decoder_attention:
                    # after the first generated id, we can subsequently re-use all key/value_states from cache
                    curr_past_key_values = layer_state.cross_attention_cache
                else:
                    curr_past_key_values = layer_state.self_attention_cache
            else:
                curr_past_key_values = layer_state

        # NOTE: FSMT has format (seq_len, BS, model_dim) for inputs
        current_states = key if self.encoder_decoder_attention else query
        if self.encoder_decoder_attention and layer_state is not None and is_updated:
            # reuse k,v, cross_attentions
            key_states = curr_past_key_values.layers[self.layer_idx].keys
            value_states = curr_past_key_values.layers[self.layer_idx].values
        else:
            key_states = self.k_proj(current_states)
            value_states = self.v_proj(current_states)
            key_states = key_states.view(-1, bsz, self.num_heads, self.head_dim).permute(1, 2, 0, 3)
            value_states = value_states.view(-1, bsz, self.num_heads, self.head_dim).permute(1, 2, 0, 3)

            if layer_state is not None:
                # save all key/value_states to cache to be re-used for fast auto-regressive generation
                key_states, value_states = curr_past_key_values.update(key_states, value_states, self.layer_idx)
                # set flag that curr layer for cross-attn is already updated so we can re-use in subsequent calls
                if self.encoder_decoder_attention:
                    layer_state.is_updated[self.layer_idx] = True

        query_states = self.q_proj(query) * self.scaling

        # Reshape back to 3D tensors for `bmm`
        query_states = query_states.view(-1, bsz * self.num_heads, self.head_dim).transpose(0, 1)
        key_states = key_states.reshape(bsz * self.num_heads, -1, self.head_dim)
        value_states = value_states.reshape(bsz * self.num_heads, -1, self.head_dim)

        assert key_states is not None
        src_len = key_states.size(1)
        attn_weights = torch.bmm(query_states, key_states.transpose(1, 2))
        assert attn_weights.size() == (bsz * self.num_heads, tgt_len, src_len)

        if attn_mask is not None:
            attn_weights = attn_weights.view(bsz, self.num_heads, tgt_len, src_len) + attn_mask
            attn_weights = attn_weights.view(bsz * self.num_heads, tgt_len, src_len)

        # This is part of a workaround to get around fork/join parallelism not supporting Optional types.
        if key_padding_mask is not None and key_padding_mask.dim() == 0:
            key_padding_mask = None
        assert key_padding_mask is None or key_padding_mask.size()[:2] == (
            bsz,
            src_len,
        )

        if key_padding_mask is not None:  # don't attend to padding symbols
            attn_weights = attn_weights.view(bsz, self.num_heads, tgt_len, src_len)
            reshaped = key_padding_mask.unsqueeze(1).unsqueeze(2)
            attn_weights = attn_weights.masked_fill(reshaped, torch.finfo(attn_weights.dtype).min)
            attn_weights = attn_weights.view(bsz * self.num_heads, tgt_len, src_len)

        attn_weights = nn.functional.softmax(attn_weights, dim=-1)

        if output_attentions:
            # make sure that attn_weights are included in graph
            attn_weights_reshaped = attn_weights.view(bsz, self.num_heads, tgt_len, src_len)
            attn_weights = attn_weights_reshaped.view(bsz * self.num_heads, tgt_len, src_len)
        else:
            attn_weights_reshaped = None

        attn_probs = nn.functional.dropout(
            attn_weights,
            p=self.dropout,
            training=self.training,
        )

        assert value_states is not None
        attn_output = torch.bmm(attn_probs, value_states)
        assert attn_output.size() == (bsz * self.num_heads, tgt_len, self.head_dim)
        attn_output = attn_output.transpose(0, 1).contiguous().view(tgt_len, bsz, embed_dim)
        attn_output = self.out_proj(attn_output)

        return attn_output, attn_weights_reshaped