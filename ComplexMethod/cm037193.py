def forward(
        self,
        layer: torch.nn.Module,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: torch.Tensor,
        attn_metadata: RocmAttentionMetadata,
        output: torch.Tensor,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass with FlashAttention.

        Args:
            query: shape = [num_tokens, num_heads, head_size]
            key: shape = [num_tokens, num_kv_heads, head_size]
            value: shape = [num_tokens, num_kv_heads, head_size]
            kv_cache: shape =
                [2, num_blocks, block_size, num_kv_heads, head_size]
            attn_metadata: Metadata for attention.
        Returns:
            shape = [num_tokens, num_heads * head_size]
        """
        if output_block_scale is not None:
            raise NotImplementedError(
                "fused block_scale output quantization is not yet supported"
                " for RocmAttentionImpl"
            )

        if attn_metadata is None:
            # Profiling run.
            return output.fill_(0)

        assert attn_metadata.use_cascade is False

        # IMPORTANT!
        # NOTE(woosuk): With piece-wise CUDA graphs, this method is executed in
        # eager-mode PyTorch. Thus, we need to be careful about any CPU overhead
        # in this method. For example, `view` and `slice` (or `[:n]`) operations
        # are surprisingly slow even in the case they do not invoke any GPU ops.
        # Minimize the PyTorch ops in this method as much as possible.
        # Whenever making a change in this method, please benchmark the
        # performance to make sure it does not introduce any overhead.

        num_actual_tokens = attn_metadata.num_actual_tokens

        if self.attn_type in (AttentionType.ENCODER_ONLY, AttentionType.ENCODER):
            return self._forward_encoder_attention(
                query[:num_actual_tokens],
                key[:num_actual_tokens],
                value[:num_actual_tokens],
                output[:num_actual_tokens],
                attn_metadata,
                layer,
            )

        key_cache, value_cache = PagedAttention.split_kv_cache(
            kv_cache, self.num_kv_heads, self.head_size
        )

        if is_quantized_kv_cache(self.kv_cache_dtype):
            key_cache = key_cache.view(self.fp8_dtype)
            value_cache = value_cache.view(self.fp8_dtype)
            assert layer._q_scale_float == 1.0, (
                "A non 1.0 q_scale is not currently supported."
            )

        cu_seqlens_q = attn_metadata.query_start_loc
        seqused_k = attn_metadata.seq_lens
        max_seqlen_q = attn_metadata.max_query_len
        max_seqlen_k = attn_metadata.max_seq_len
        block_table = attn_metadata.block_table

        # Compute attention and update output up to `num_actual_tokens`.
        chunked_prefill_paged_decode(
            query=query[:num_actual_tokens],
            key=key[:num_actual_tokens] if key is not None else None,
            value=value[:num_actual_tokens] if value is not None else None,
            output=output[:num_actual_tokens],
            kv_cache_dtype=self.kv_cache_dtype,
            key_cache=key_cache,
            value_cache=value_cache,
            block_table=block_table,
            query_start_loc=cu_seqlens_q,
            seq_lens=seqused_k,
            max_seq_len=max_seqlen_k,
            max_query_len=max_seqlen_q,
            k_scale=layer._k_scale,
            v_scale=layer._v_scale,
            alibi_slopes=self.alibi_slopes,
            sliding_window=self.sliding_window[0],
            sm_scale=self.scale,
            output_scale=output_scale,
            sinks=self.sinks,
            causal=attn_metadata.causal,
        )

        return output