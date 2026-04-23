def forward(
        self,
        hidden_states,
        encoder_hidden_states=None,
        attention_mask=None,
        position_embeddings=None,
    ):
        bsz, q_len, _ = hidden_states.size()

        query_states = self.q_proj(hidden_states)
        query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim)
        query_states = self.q_norm(query_states)
        query_states = query_states.transpose(1, 2)

        if self.is_cross_attention and encoder_hidden_states is not None:
            bsz_enc, kv_len, _ = encoder_hidden_states.size()
            key_states = self.k_proj(encoder_hidden_states)
            value_states = self.v_proj(encoder_hidden_states)

            key_states = key_states.view(bsz_enc, kv_len, self.num_kv_heads, self.head_dim)
            key_states = self.k_norm(key_states)
            value_states = value_states.view(bsz_enc, kv_len, self.num_kv_heads, self.head_dim)

            key_states = key_states.transpose(1, 2)
            value_states = value_states.transpose(1, 2)
        else:
            kv_len = q_len
            key_states = self.k_proj(hidden_states)
            value_states = self.v_proj(hidden_states)

            key_states = key_states.view(bsz, q_len, self.num_kv_heads, self.head_dim)
            key_states = self.k_norm(key_states)
            value_states = value_states.view(bsz, q_len, self.num_kv_heads, self.head_dim)

            key_states = key_states.transpose(1, 2)
            value_states = value_states.transpose(1, 2)

            if position_embeddings is not None:
                cos, sin = position_embeddings
                query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)

        n_rep = self.num_heads // self.num_kv_heads
        if n_rep > 1:
            key_states = key_states.repeat_interleave(n_rep, dim=1)
            value_states = value_states.repeat_interleave(n_rep, dim=1)

        attn_bias = None
        if self.sliding_window is not None and not self.is_cross_attention:
            indices = torch.arange(q_len, device=query_states.device)
            diff = indices.unsqueeze(1) - indices.unsqueeze(0)
            in_window = torch.abs(diff) <= self.sliding_window

            window_bias = torch.zeros((q_len, kv_len), device=query_states.device, dtype=query_states.dtype)
            min_value = torch.finfo(query_states.dtype).min
            window_bias.masked_fill_(~in_window, min_value)

            window_bias = window_bias.unsqueeze(0).unsqueeze(0)

            if attn_bias is not None:
                if attn_bias.dtype == torch.bool:
                    base_bias = torch.zeros_like(window_bias)
                    base_bias.masked_fill_(~attn_bias, min_value)
                    attn_bias = base_bias + window_bias
                else:
                    attn_bias = attn_bias + window_bias
            else:
                attn_bias = window_bias

        attn_output = optimized_attention(query_states, key_states, value_states, self.num_heads, attn_bias, skip_reshape=True, low_precision_attention=False)
        attn_output = self.o_proj(attn_output)

        return attn_output