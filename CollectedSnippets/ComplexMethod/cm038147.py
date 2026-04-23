def _forward(
        self,
        hidden_states: torch.Tensor,
        output: torch.Tensor,
        positions: torch.Tensor,
    ) -> None:
        """Actual forward implementation."""
        forward_context = get_forward_context()
        attn_metadata: AttentionMetadata = forward_context.attn_metadata
        if attn_metadata is not None:
            assert isinstance(attn_metadata, dict)
            attn_metadata = attn_metadata[self.prefix]
            assert isinstance(attn_metadata, LinearAttentionMetadata)
            num_actual_tokens = (
                attn_metadata.num_prefill_tokens + attn_metadata.num_decode_tokens
            )
        else:
            num_actual_tokens = hidden_states.shape[0]

        # QKV projection
        qkv, _ = self.query_key_value(hidden_states[:num_actual_tokens])

        # use rotary_emb support fp32
        qkv = qkv.to(torch.float32)
        if self.linear_silu:
            qkv = F.silu(qkv)

        # Split q, k, v
        q, k, v = torch.split(
            qkv,
            [self.q_size_per_rank, self.kv_size_per_rank, self.kv_size_per_rank],
            dim=-1,
        )

        # Apply QK norm if needed
        if self.use_qk_norm:
            q = q.reshape(-1, self.tp_heads, self.head_dim)
            k = k.reshape(-1, self.tp_kv_heads, self.head_dim)
            q = layernorm_fn(
                q,
                self.query_layernorm.weight.data,
                bias=None,
                eps=self.rms_norm_eps,
                is_rms_norm=True,
            )
            k = layernorm_fn(
                k,
                self.key_layernorm.weight.data,
                bias=None,
                eps=self.rms_norm_eps,
                is_rms_norm=True,
            )
            q = q.reshape(-1, self.q_size_per_rank)
            k = k.reshape(-1, self.kv_size_per_rank)

        # Apply rotary embeddings
        if self.linear_rope:
            q, k = self.rotary_emb(positions[:num_actual_tokens], q, k)

        # Reshape to [batch, heads, seq_len, head_dim]
        q = q.view((qkv.shape[0], self.tp_heads, self.head_dim))
        k = k.view((qkv.shape[0], self.tp_kv_heads, self.head_dim))
        v = v.view((qkv.shape[0], self.tp_kv_heads, self.head_dim))

        # Apply scaling if using minimax backend
        if self.linear_scale:
            q = q * self.scaling

        # Get KV cache and state indices
        if attn_metadata is not None:
            kv_cache = self.kv_cache[0]
            state_indices_tensor = attn_metadata.state_indices_tensor
            clear_linear_attention_cache_for_new_sequences(
                kv_cache, state_indices_tensor, attn_metadata
            )

        # Compute attention
        decode_only = getattr(attn_metadata, "num_prefills", 0) == 0
        if attn_metadata is None:
            hidden = torch.empty(
                (q.shape[0], q.shape[1] * q.shape[2]), device=q.device, dtype=q.dtype
            )
        else:
            if not decode_only:
                hidden = self._prefill_and_mix_infer(
                    q, k, v, kv_cache, state_indices_tensor, attn_metadata
                )
            else:
                hidden = self._decode_infer(
                    q, k, v, kv_cache, state_indices_tensor, attn_metadata
                )

        # Apply group norm and gate (matching SGLang behavior)
        gate, _ = self.g_proj(hidden_states[:num_actual_tokens])

        if self.group_norm_size > 1:
            hidden = self.g_norm(hidden, gate)
        else:
            hidden = self.g_norm(hidden)
            hidden = F.sigmoid(gate) * hidden

        hidden = hidden.to(hidden_states.dtype)

        # Output projection
        dense_out, _ = self.dense(hidden)
        output[:num_actual_tokens] = dense_out