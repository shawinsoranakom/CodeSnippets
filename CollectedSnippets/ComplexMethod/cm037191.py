def forward(
        self,
        layer: torch.nn.Module,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: torch.Tensor,
        attn_metadata: AiterFlashAttentionMetadata,
        output: torch.Tensor,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass with AiterFlashAttention.

        Args:
            query: shape = [num_tokens, num_heads, head_size]
            key: shape = [num_tokens, num_kv_heads, head_size]
            value: shape = [num_tokens, num_kv_heads, head_size]
            kv_cache: shape =
                [2, num_blocks, block_size, num_kv_heads, head_size]
            attn_metadata: Metadata for attention.
        Returns:
            shape = [num_tokens, num_heads * head_size]
        NOTE: FP8 quantization, flash-attn expect the size of
              {q,k,v}_descale to be (num_sequences, num_kv_heads).
              We use torch's .expand() to avoid duplicating values
        """
        if output_scale is not None or output_block_scale is not None:
            raise NotImplementedError(
                "fused output quantization is not yet supported "
                "for AiterFlashAttentionImpl"
            )

        if attn_metadata is None:
            # Profiling run.
            return output.fill_(0)

        # IMPORTANT!
        # NOTE(woosuk): With piece-wise CUDA graphs, this method is
        # executed in eager-mode PyTorch. Thus, we need to be careful
        # about any CPU overhead in this method. For example, `view`
        # and `slice` (or `[:n]`) operations are surprisingly slow even
        # in the case they do not invoke any GPU ops.
        # Minimize the PyTorch ops in this method as much as possible.
        # Whenever making a change in this method, please benchmark the
        # performance to make sure it does not introduce any overhead.
        num_actual_tokens = attn_metadata.num_actual_tokens
        key_cache, value_cache = kv_cache.unbind(0)

        if is_quantized_kv_cache(self.kv_cache_dtype):
            key_cache = key_cache.view(current_platform.fp8_dtype())
            value_cache = value_cache.view(current_platform.fp8_dtype())

        # decode:extend:prefill
        query = query[:num_actual_tokens]
        if key is not None:
            key = key[:num_actual_tokens]
        if value is not None:
            value = value[:num_actual_tokens]

        output_actual_tokens = output[:num_actual_tokens]

        num_decodes = attn_metadata.num_decodes
        num_prefills = attn_metadata.num_prefills
        num_extends = attn_metadata.num_extends

        num_decode_tokens = attn_metadata.num_decode_tokens
        num_extend_tokens = attn_metadata.num_extend_tokens
        if not attn_metadata.use_cascade:
            # calculate for pure prefills
            if num_prefills > 0:
                assert attn_metadata.prefill_metadata is not None

                prefill_query = query[num_decode_tokens + num_extend_tokens :]
                prefill_key = key[num_decode_tokens + num_extend_tokens :]
                prefill_value = value[num_decode_tokens + num_extend_tokens :]

                rocm_aiter_ops.flash_attn_varlen_func(
                    q=prefill_query,
                    k=prefill_key,
                    v=prefill_value,
                    cu_seqlens_q=attn_metadata.prefill_metadata.query_start_loc,
                    cu_seqlens_k=attn_metadata.prefill_metadata.query_start_loc,
                    max_seqlen_q=attn_metadata.prefill_metadata.max_query_len,
                    max_seqlen_k=attn_metadata.prefill_metadata.max_seq_len,
                    min_seqlen_q=1,
                    dropout_p=0.0,
                    softmax_scale=self.scale,
                    causal=attn_metadata.causal,
                    window_size=self.sliding_window,
                    alibi_slopes=self.alibi_slopes,
                    out=output_actual_tokens[num_decode_tokens + num_extend_tokens :],
                )

            # calculate for extends
            if num_extends > 0:
                assert attn_metadata.extend_metadata is not None
                extend_tokens_slice = slice(
                    num_decode_tokens, num_decode_tokens + num_extend_tokens
                )
                extend_queries = query[extend_tokens_slice]
                extend_keys = key[extend_tokens_slice]
                extend_values = value[extend_tokens_slice]
                extend_outputs = output[extend_tokens_slice]
                k_scale = layer._k_scale
                v_scale = layer._v_scale
                if rocm_aiter_ops.is_shuffle_kv_cache_enabled():
                    k_scale = attn_metadata.k_scale
                    v_scale = attn_metadata.v_scale
                self.extend_forward(
                    attn_metadata=attn_metadata,
                    query=extend_queries,
                    key=extend_keys,
                    value=extend_values,
                    key_cache=key_cache,
                    value_cache=value_cache,
                    output=extend_outputs,
                    cu_seqlens_q=attn_metadata.extend_metadata.query_start_loc,
                    max_seqlen_q=attn_metadata.extend_metadata.max_query_len,
                    max_seqlen_k=attn_metadata.extend_metadata.max_seq_len,
                    min_seqlen_q=1,
                    block_table=attn_metadata.block_table[
                        num_decodes : num_decodes + num_extends
                    ],
                    slot_mapping=attn_metadata.slot_mapping[
                        num_decodes : num_decodes + num_extends
                    ],
                    k_scale=k_scale,
                    v_scale=v_scale,
                )

            # calculate for decodes
            if num_decodes > 0:
                assert attn_metadata.decode_metadata is not None
                decode_max_query_len = attn_metadata.decode_metadata.max_query_len

                # Multi-token speculative decode path.
                if decode_max_query_len > 1:
                    assert not rocm_aiter_ops.is_shuffle_kv_cache_enabled(), (
                        "Shuffle KV cache layout is not supported with "
                        "speculative decoding (multi-token decode)."
                    )
                    if not attn_metadata.causal:
                        from aiter.ops.triton.attention.mha_v3 import (
                            flash_attn_with_kvcache,
                        )

                        descale_shape = (num_decodes, key_cache.shape[2])
                        decode_query = query[:num_decode_tokens].reshape(
                            num_decodes,
                            decode_max_query_len,
                            query.shape[1],
                            query.shape[2],
                        )
                        decode_out = flash_attn_with_kvcache(
                            q=decode_query,
                            k_cache=key_cache,
                            v_cache=value_cache,
                            cache_seqlens=attn_metadata.seq_lens[:num_decodes],
                            softmax_scale=self.scale,
                            causal=attn_metadata.causal,
                            window_size=self.sliding_window,
                            softcap=self.logits_soft_cap,
                            q_descale=None,
                            k_descale=layer._k_scale.expand(descale_shape),
                            v_descale=layer._v_scale.expand(descale_shape),
                            page_table=attn_metadata.block_table[:num_decodes],
                        )
                        output[:num_decode_tokens].copy_(
                            decode_out.reshape(
                                num_decode_tokens,
                                query.shape[1],
                                query.shape[2],
                            )
                        )
                    else:
                        # Non-uniform query lengths can appear in real serving
                        # traffic (e.g. mixed datasets). Fall back to varlen
                        # unified_attention instead of asserting.
                        from aiter.ops.triton.unified_attention import (
                            unified_attention,
                        )

                        descale_shape = (
                            num_decodes,
                            key_cache.shape[2],
                        )
                        unified_attention(
                            q=query[:num_decode_tokens],
                            k=key_cache,
                            v=value_cache,
                            out=output[:num_decode_tokens],
                            cu_seqlens_q=attn_metadata.query_start_loc[
                                : num_decodes + 1
                            ],
                            max_seqlen_q=decode_max_query_len,
                            seqused_k=attn_metadata.seq_lens[:num_decodes],
                            max_seqlen_k=attn_metadata.max_seq_len,
                            softmax_scale=self.scale,
                            causal=True,
                            alibi_slopes=self.alibi_slopes,
                            window_size=self.sliding_window,
                            block_table=attn_metadata.block_table[:num_decodes],
                            softcap=self.logits_soft_cap,
                            q_descale=None,
                            k_descale=layer._k_scale.expand(descale_shape),
                            v_descale=layer._v_scale.expand(descale_shape),
                        )
                    return

                # The ll4mi kernel in paged_attention_v1 requires
                # HEAD_SIZE >= 16 * NWARPS (= 64 on ROCm with NWARPS=4).
                # For smaller head sizes or sliding window attention,
                # fall back to the unified_attention triton kernel which
                # handles both correctly.
                _MIN_HEAD_SIZE_FOR_LL4MI = 64
                use_unified_attention = self.head_size < _MIN_HEAD_SIZE_FOR_LL4MI

                if use_unified_attention:
                    assert not rocm_aiter_ops.is_shuffle_kv_cache_enabled(), (
                        "unified_attention fallback with shuffle layout "
                        "is not supported yet."
                    )
                    from aiter.ops.triton.unified_attention import (
                        unified_attention,
                    )

                    decode_cu_seqlens_q = attn_metadata.query_start_loc[
                        : num_decodes + 1
                    ]
                    descale_shape = (
                        num_decodes,
                        key_cache.shape[2],
                    )
                    unified_attention(
                        q=query[:num_decode_tokens],
                        k=key_cache,
                        v=value_cache,
                        out=output[:num_decode_tokens],
                        cu_seqlens_q=decode_cu_seqlens_q,
                        max_seqlen_q=1,
                        seqused_k=attn_metadata.seq_lens[:num_decodes],
                        max_seqlen_k=attn_metadata.max_seq_len,
                        softmax_scale=self.scale,
                        causal=True,
                        alibi_slopes=self.alibi_slopes,
                        window_size=self.sliding_window,
                        block_table=attn_metadata.block_table[:num_decodes],
                        softcap=self.logits_soft_cap,
                        q_descale=None,
                        k_descale=layer._k_scale.expand(descale_shape),
                        v_descale=layer._v_scale.expand(descale_shape),
                    )
                elif rocm_aiter_ops.is_shuffle_kv_cache_enabled():
                    _, num_heads, head_size = query.shape
                    num_seqs = attn_metadata.seq_lens.shape[0]
                    max_num_partitions = (
                        attn_metadata.max_seq_len + _PARTITION_SIZE_ROCM - 1
                    ) // _PARTITION_SIZE_ROCM
                    tmp_out = torch.empty(
                        (num_seqs, num_heads, max_num_partitions, head_size),
                        dtype=query.dtype,
                        device=query.device,
                    )
                    exp_sums = torch.empty(
                        (num_seqs, num_heads, max_num_partitions),
                        dtype=torch.float32,
                        device=query.device,
                    )
                    max_logits = torch.empty_like(exp_sums)
                    num_blocks, block_size, num_kv_heads, _ = key_cache.shape
                    x = 16 // key_cache.element_size()
                    k_cache_template = torch.empty(
                        [num_blocks, num_kv_heads, head_size // x, block_size, x],
                        dtype=key_cache.dtype,
                        device="meta",
                    )
                    v_cache_template = torch.empty(
                        [num_blocks, num_kv_heads, block_size // x, head_size, x],
                        dtype=value_cache.dtype,
                        device="meta",
                    )
                    new_key_cache = key_cache.view_as(k_cache_template)
                    new_value_cache = value_cache.view_as(v_cache_template)
                    k_qscale = (
                        layer._k_scale
                        if attn_metadata.k_scale is None
                        else attn_metadata.k_scale
                    )
                    v_qscale = (
                        layer._v_scale
                        if attn_metadata.v_scale is None
                        else attn_metadata.v_scale
                    )
                    rocm_aiter_ops.paged_attention_common(
                        Q=query[:num_decode_tokens],
                        K=new_key_cache,
                        V=new_value_cache,
                        tmp_out=tmp_out,
                        max_logits=max_logits,
                        exp_sums=exp_sums,
                        max_seq_len=attn_metadata.max_seq_len,
                        block_tables=attn_metadata.block_table[:num_decodes],
                        context_lens=attn_metadata.seq_lens[:num_decodes],
                        block_tables_stride0=attn_metadata.block_table[
                            :num_decodes
                        ].stride(0),
                        scale=self.scale,
                        K_QScale_hip=k_qscale,
                        V_QScale_hip=v_qscale,
                        K_QScale_asm=k_qscale,
                        V_QScale_asm=v_qscale,
                        out_=output[:num_decode_tokens],
                        kv_cache_dtype=self.kv_cache_dtype,
                    )
                else:
                    _, num_heads, head_size = query.shape
                    nbytes_per_qo_elem = torch.finfo(query.dtype).bits // 8
                    num_seqs = attn_metadata.seq_lens.shape[0]
                    max_num_partitions = (
                        attn_metadata.max_seq_len + _PARTITION_SIZE_ROCM - 1
                    ) // _PARTITION_SIZE_ROCM

                    workspace_buffer = torch.empty(
                        (num_seqs * num_heads * max_num_partitions * head_size)
                        * nbytes_per_qo_elem
                        + 2 * (num_seqs * num_heads * max_num_partitions) * 4,
                        dtype=torch.uint8,
                        device=output.device,
                    )

                    # import so that aiter register the op to the namespace of
                    # torch.ops.aiter
                    import aiter  # noqa: F401

                    torch.ops.aiter.paged_attention_v1(
                        output[:num_decode_tokens],
                        workspace_buffer,
                        query[:num_decode_tokens],
                        key_cache,
                        value_cache,
                        self.scale,
                        attn_metadata.block_table[:num_decodes],
                        attn_metadata.query_start_loc[:num_decodes],
                        attn_metadata.seq_lens[:num_decodes],
                        attn_metadata.max_seq_len,
                        self.alibi_slopes,
                        self.kv_cache_dtype,
                        "NHD",
                        self.logits_soft_cap,
                        layer._k_scale,
                        layer._v_scale,
                        None,
                        _PARTITION_SIZE_ROCM,
                        1,
                        self.sliding_window[0] + 1,
                    )
        else:
            raise NotImplementedError(
                "Cascade attention is not implemented for ROCM AITER"
            )

        return output