def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: CommonAttentionMetadata,
        fast_build: bool = False,
    ) -> FlexAttentionMetadata:
        num_reqs = common_attn_metadata.num_reqs
        num_actual_tokens = common_attn_metadata.num_actual_tokens
        max_query_len = common_attn_metadata.max_query_len

        max_seq_len = common_attn_metadata.max_seq_len
        query_start_loc = common_attn_metadata.query_start_loc
        seq_lens = common_attn_metadata.seq_lens
        block_table_tensor = common_attn_metadata.block_table_tensor
        slot_mapping = common_attn_metadata.slot_mapping
        num_blocks_per_seq = cdiv(seq_lens, self.block_size)

        use_cascade = common_prefix_len > 0
        cu_prefix_query_lens = None
        prefix_kv_lens = None
        suffix_kv_lens = None
        if use_cascade:
            raise NotImplementedError(
                "Cascade prefix attention is not yet implemented "
                "for FlexAttention backend"
            )

        block_size = self.kv_cache_spec.block_size
        max_possible_seq_len = self.model_config.max_model_len
        num_gpu_blocks = self.cache_config.num_gpu_blocks

        assert num_gpu_blocks is not None, (
            "FlexAttention requires num_gpu_blocks to be set"
        )
        total_cache_tokens = num_gpu_blocks * block_size

        inverse_block_table = physical_to_logical_mapping(
            block_table_tensor, seq_lens, block_size, num_gpu_blocks
        )
        if self.persistent_physical_to_logical is None:
            max_num_seqs = self.vllm_config.scheduler_config.max_num_seqs
            self.persistent_physical_to_logical = torch.empty(
                max_num_seqs,
                num_gpu_blocks,
                dtype=torch.long,
                device=self.device,
            )

        if self.persistent_kv_indices is None:
            self.persistent_kv_indices = torch.empty(
                self.max_num_query_groups,
                self.max_num_kv_indices,
                dtype=torch.int32,
                device=self.device,
            )

        inverse_block_table = copy_to_persistent(
            self.persistent_physical_to_logical, inverse_block_table
        )

        offset_tensor = common_attn_metadata.compute_num_computed_tokens()
        offset_tensor = copy_to_persistent(self.persistent_offset_tensor, offset_tensor)

        uses_paged_kv = not isinstance(self.kv_cache_spec, EncoderOnlyAttentionSpec)
        logical_mask_mod = (
            bidirectional_mask_mod
            if uses_paged_kv and not common_attn_metadata.causal
            else causal_mask_mod
        )

        out = FlexAttentionMetadata(
            causal=common_attn_metadata.causal,
            logical_mask_mod=logical_mask_mod,
            num_actual_tokens=num_actual_tokens,
            max_query_len=max_query_len,
            query_start_loc=query_start_loc,
            max_seq_len=max_seq_len,
            seq_lens=seq_lens,
            block_table=block_table_tensor,
            slot_mapping=slot_mapping,
            use_cascade=use_cascade,
            common_prefix_len=common_prefix_len,
            cu_prefix_query_lens=cu_prefix_query_lens,
            prefix_kv_lens=prefix_kv_lens,
            suffix_kv_lens=suffix_kv_lens,
            block_size=block_size,
            max_possible_sequence_length=max_possible_seq_len,
            num_reqs=num_reqs,
            physical_to_logical=inverse_block_table,
            total_cache_tokens=total_cache_tokens,
            decode_offset=offset_tensor,
            num_blocks_per_seq=num_blocks_per_seq,
            uses_paged_kv=uses_paged_kv,
            # FIXME(Isotr0py): direct build has issue to build bidirectional
            # attention block mask for encoder-only models, disable it temporarily.
            # see: https://github.com/vllm-project/vllm/pull/27329#issuecomment-3431484053
            direct_build=self.direct_build and uses_paged_kv,
            q_block_size=self.q_block_size,
            kv_block_size=self.kv_block_size,
            persistent_kv_indices=self.persistent_kv_indices,
            persistent_kv_num_blocks=self.persistent_kv_num_blocks,
            persistent_doc_ids=self.persistent_doc_ids,
        )

        # Pre-build block_mask so it is ready before CUDA graph capture.
        # Without this, the lazy build in forward() would run non-graph-safe
        # ops (e.g. torch.nonzero) inside capture.
        if out.block_mask is None:
            if out.direct_build:
                out.block_mask = out._build_block_mask_direct()
            else:
                out.block_mask = out.build_block_mask()

        return out