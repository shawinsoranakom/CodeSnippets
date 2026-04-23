def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: CommonAttentionMetadata,
        fast_build: bool = False,
    ) -> FlashAttentionMetadata:
        """
        fast_build disables AOT scheduling, used when there will be few
        iterations i.e. spec-decode
        """
        num_reqs = common_attn_metadata.num_reqs
        num_actual_tokens = common_attn_metadata.num_actual_tokens
        max_query_len = common_attn_metadata.max_query_len
        max_seq_len = common_attn_metadata.max_seq_len
        query_start_loc = common_attn_metadata.query_start_loc
        seq_lens = common_attn_metadata.seq_lens
        block_table_tensor = common_attn_metadata.block_table_tensor
        slot_mapping = common_attn_metadata.slot_mapping
        causal = common_attn_metadata.causal

        # Disable AOT schedule for spec-decode proposer (not worth the overhead)
        # and for batch invariance (schedule varies with max_seqlen_q/k).
        aot_schedule = (
            self.aot_schedule and not fast_build and not envs.VLLM_BATCH_INVARIANT
        )

        if self.aot_sliding_window is None:
            self.aot_sliding_window = (-1, -1)
            # For the AOT scheduler we need the sliding window value to be
            # constant for all layers to. We have to populate this on the first
            # build() call so the layers are constructed (cannot populate)
            # in __init__.
            if aot_schedule:
                sliding_window_configs = _get_sliding_window_configs(self.vllm_config)
                if len(sliding_window_configs) == 1:
                    sliding_window_config = sliding_window_configs.pop()
                    if sliding_window_config is not None:
                        self.aot_sliding_window = sliding_window_config
                elif len(sliding_window_configs) > 1:
                    self.aot_schedule = False
                    aot_schedule = False

        max_num_splits = 0  # 0 means use FA3's heuristics, not CG compatible
        if (
            self.use_full_cuda_graph
            and self.max_cudagraph_size is not None
            and num_actual_tokens <= self.max_cudagraph_size
        ):
            # NOTE(woosuk): Setting num_splits > 1 may increase the memory
            # usage, because the intermediate buffers of size [num_splits,
            # num_heads, num_tokens, head_size] are allocated. Therefore,
            # we only set num_splits when using cuda graphs.
            max_num_splits = self.max_num_splits

        if envs.VLLM_BATCH_INVARIANT:
            max_num_splits = 1

        def schedule(
            batch_size, cu_query_lens, max_query_len, seqlens, max_seq_len, causal
        ):
            cache_dtype = self.cache_config.cache_dtype
            if is_quantized_kv_cache(cache_dtype):
                qkv_dtype = FlashAttentionBackend.get_fp8_dtype_for_flashattn(
                    cache_dtype
                )
            else:
                qkv_dtype = self.kv_cache_dtype
            if aot_schedule:
                return get_scheduler_metadata(
                    batch_size=batch_size,
                    max_seqlen_q=max_query_len,
                    max_seqlen_k=max_seq_len,
                    num_heads_q=self.num_heads_q * self.dcp_world_size,
                    num_heads_kv=self.num_heads_kv,
                    headdim=self.headdim,
                    cache_seqlens=seqlens,
                    qkv_dtype=qkv_dtype,
                    cu_seqlens_q=cu_query_lens,
                    page_size=self.block_size,
                    causal=causal,
                    window_size=self.aot_sliding_window,
                    num_splits=max_num_splits,
                )
            return None

        use_cascade = common_prefix_len > 0
        max_dcp_context_kv_len = 0
        dcp_context_kv_lens = None

        cu_prefix_query_lens = None
        prefix_kv_lens = None
        suffix_kv_lens = None
        prefix_scheduler_metadata = None

        if self.dcp_world_size > 1:
            query_lens = query_start_loc[1:] - query_start_loc[:-1]
            context_kv_lens = seq_lens - query_lens
            local_context_kv_lens = get_dcp_local_seq_lens(
                context_kv_lens,
                self.dcp_world_size,
                self.dcp_rank,
                self.cp_kv_cache_interleave_size,
            )
            self._dcp_context_kv_lens[:num_reqs] = local_context_kv_lens
            self._dcp_context_kv_lens[num_reqs:] = 0
            dcp_context_kv_lens = self._dcp_context_kv_lens[:num_reqs]

            # After DCP distribution, the maximum number of tokens for any rank is
            # ceil(L / (N * I)) * I, where L is max_seq_len, N is dcp_world_size,
            # and I is cp_kv_cache_interleave_size.
            # This eliminates GPU->CPU sync while minimizing workspace over-allocation.
            num_partitions = self.dcp_world_size * self.cp_kv_cache_interleave_size
            max_dcp_context_kv_len = (
                (max_seq_len + num_partitions - 1) // num_partitions
            ) * self.cp_kv_cache_interleave_size

            scheduler_metadata = schedule(
                batch_size=num_reqs,
                cu_query_lens=query_start_loc,
                max_query_len=max_query_len,
                seqlens=dcp_context_kv_lens,
                max_seq_len=max_dcp_context_kv_len,
                causal=False,
            )
        elif use_cascade:
            cu_prefix_query_lens = torch.tensor(
                [0, num_actual_tokens], dtype=torch.int32, device=self.device
            )
            prefix_kv_lens = torch.tensor(
                [common_prefix_len], dtype=torch.int32, device=self.device
            )
            # Use GPU tensor directly - no CPU sync needed
            suffix_kv_lens = seq_lens[:num_reqs] - common_prefix_len
            prefix_scheduler_metadata = schedule(
                batch_size=1,
                cu_query_lens=cu_prefix_query_lens,
                max_query_len=num_actual_tokens,
                seqlens=prefix_kv_lens,
                max_seq_len=common_prefix_len,
                causal=False,
            )
            scheduler_metadata = schedule(
                batch_size=num_reqs,
                cu_query_lens=query_start_loc,
                max_query_len=max_query_len,
                seqlens=suffix_kv_lens,
                max_seq_len=max_seq_len - common_prefix_len,
                causal=True,
            )
        else:
            scheduler_metadata = schedule(
                batch_size=num_reqs,
                cu_query_lens=query_start_loc,
                max_query_len=max_query_len,
                seqlens=seq_lens,
                max_seq_len=max_seq_len,
                causal=causal,
            )
        # For FA3 + full cudagraph
        if self.use_full_cuda_graph and scheduler_metadata is not None:
            n = scheduler_metadata.shape[0]
            self.scheduler_metadata[:n] = scheduler_metadata
            # NOTE(woosuk): We should zero out the rest of the scheduler
            # metadata to guarantee the correctness. Otherwise, some thread
            # blocks may use the invalid scheduler metadata and overwrite the
            # output buffer.
            self.scheduler_metadata[n:] = 0
            scheduler_metadata = self.scheduler_metadata[:n]

        attn_metadata = FlashAttentionMetadata(
            num_actual_tokens=num_actual_tokens,
            max_query_len=max_query_len,
            query_start_loc=query_start_loc,
            max_seq_len=max_seq_len,
            seq_lens=seq_lens,
            block_table=block_table_tensor,
            slot_mapping=slot_mapping,
            max_dcp_context_kv_len=max_dcp_context_kv_len,
            dcp_context_kv_lens=dcp_context_kv_lens,
            use_cascade=use_cascade,
            common_prefix_len=common_prefix_len,
            scheduler_metadata=scheduler_metadata,
            cu_prefix_query_lens=cu_prefix_query_lens,
            prefix_kv_lens=prefix_kv_lens,
            suffix_kv_lens=suffix_kv_lens,
            prefix_scheduler_metadata=prefix_scheduler_metadata,
            max_num_splits=max_num_splits,
            causal=causal,
        )
        return attn_metadata