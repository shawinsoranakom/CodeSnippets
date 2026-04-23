def forward(
        self,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Cache | None = None,
        prev_topk_indices: torch.Tensor | None = None,
        **kwargs: Unpack[FlashAttentionKwargs],
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        batch_size, seq_length = hidden_states.shape[:-1]
        cos, sin = position_embeddings

        # ===== Query path =====
        if self.q_lora_rank is None:
            query_states = self.q_proj(hidden_states)
            q_resid = None
        else:
            q_resid = self.q_a_layernorm(self.q_a_proj(hidden_states))  # [B, S, q_lora_rank]
            query_states = self.q_b_proj(q_resid)
        query_states = query_states.view(batch_size, seq_length, -1, self.qk_head_dim).transpose(1, 2)
        # Split nope/rope, apply RoPE, recombine — layout: [B, H, S, D]
        q_nope, q_pe = torch.split(query_states, [self.qk_nope_head_dim, self.qk_rope_head_dim], dim=-1)
        q_pe = apply_rotary_pos_emb(q_pe, cos, sin, unsqueeze_dim=1)  # BHSD format

        # ===== KV path =====
        compressed_kv = self.kv_a_proj_with_mqa(hidden_states)  # [B, S, kv_rank + rope_D]
        k_compressed, k_pe = torch.split(compressed_kv, [self.kv_lora_rank, self.qk_rope_head_dim], dim=-1)
        k_compressed = self.kv_a_layernorm(k_compressed)  # [B, S, kv_rank]

        # Expand KV through kv_b_proj
        kv_expanded = self.kv_b_proj(k_compressed)  # [B, S, H * (nope_D + v_D)]
        kv_expanded = kv_expanded.view(batch_size, seq_length, -1, self.qk_nope_head_dim + self.v_head_dim)
        k_nope, value_states = torch.split(kv_expanded, [self.qk_nope_head_dim, self.v_head_dim], dim=-1)
        k_nope = k_nope.transpose(1, 2)  # [B, H, S, nope_D]
        value_states = value_states.transpose(1, 2)  # [B, H, S, v_D]

        # RoPE on k_pe (single-head rope stream)
        k_pe = k_pe.view(batch_size, 1, seq_length, self.qk_rope_head_dim)  # [B, 1, S, rope_D]
        k_pe = apply_rotary_pos_emb(k_pe, cos, sin, unsqueeze_dim=1)  # BHSD format
        k_pe = k_pe.expand(-1, k_nope.shape[1], -1, -1)  # [B, H, S, rope_D]

        # Assemble full Q and K
        query_states = torch.cat([q_nope, q_pe], dim=-1)  # [B, H, S, qk_head_dim]
        key_states = torch.cat([k_nope, k_pe], dim=-1)  # [B, H, S, qk_head_dim]

        # Cache update
        if past_key_values is not None:
            key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)

        # ===== Indexer (DSA sparse mask) =====
        # attention_mask is [B, 1, S, T] (4D) for eager and (2D) otherwise but indexer works with [B, S, T] (3D)
        if not self.skip_topk or prev_topk_indices is None:
            indexer_mask = (
                attention_mask[:, 0, :, :]
                if attention_mask is not None and attention_mask.dim() == 4
                else attention_mask.unsqueeze(1)
                if attention_mask is not None
                else None
            )
            topk_indices = self.indexer(
                hidden_states,
                q_resid,
                position_embeddings,
                indexer_mask,
                use_cache=past_key_values is not None,
            )  # [B, S, topk]
        else:
            topk_indices = prev_topk_indices  # [B, S, topk]

        # Build combined DSA + causal mask: -inf everywhere except selected top-k positions
        total_len = key_states.shape[2]
        index_mask = torch.full(
            (batch_size, seq_length, total_len),
            float("-inf"),
            device=hidden_states.device,
            dtype=query_states.dtype,
        )
        index_mask.scatter_(-1, topk_indices, 0.0)  # [B, S, T]
        index_mask = index_mask.unsqueeze(1)  # [B, 1, S, T]
        if attention_mask is not None and attention_mask.dim() == 4:
            causal_mask = attention_mask[..., :total_len]
            combined_mask = index_mask + causal_mask
        else:
            combined_mask = (
                attention_mask.masked_fill(index_mask == float("-inf"), float("-inf"))
                if attention_mask is not None
                else index_mask
            )

        # Flash attention head_dim padding (qk_head_dim != v_head_dim)
        if is_flash_attention_requested(self.config) and self.qk_head_dim != self.v_head_dim:
            value_states = F.pad(value_states, [0, self.qk_head_dim - self.v_head_dim])

        attention_interface: Callable = ALL_ATTENTION_FUNCTIONS.get_interface(
            self.config._attn_implementation, eager_attention_forward
        )

        attn_output, attn_weights = attention_interface(
            self,
            query_states,
            key_states,
            value_states,
            combined_mask,
            dropout=0.0 if not self.training else self.attention_dropout,
            scaling=self.scaling,
            indices=topk_indices,  # flash_mla_with_kvcache
            **kwargs,
        )

        if is_flash_attention_requested(self.config) and self.qk_head_dim != self.v_head_dim:
            attn_output = attn_output[:, :, :, : self.v_head_dim]

        attn_output = attn_output.reshape(batch_size, seq_length, -1).contiguous()
        attn_output = self.o_proj(attn_output)
        return attn_output, attn_weights, topk_indices if self.next_skip_topk else None