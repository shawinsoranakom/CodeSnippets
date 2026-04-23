def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: CommonAttentionMetadata,
        fast_build: bool = False,
    ) -> DeepseekV32IndexerMetadata:
        num_reqs = common_attn_metadata.num_reqs
        num_tokens = common_attn_metadata.num_actual_tokens

        query_start_loc_cpu = common_attn_metadata.query_start_loc_cpu
        num_decodes, num_prefills, num_decode_tokens, num_prefill_tokens = (
            split_decodes_and_prefills(
                common_attn_metadata,
                decode_threshold=self.reorder_batch_threshold,
                require_uniform=not self.use_flattening,
            )
        )

        assert num_decodes + num_prefills == num_reqs
        assert num_decode_tokens + num_prefill_tokens == num_tokens

        prefill_metadata = None
        if num_prefills > 0:
            prefill_query_lens_cpu = torch.diff(
                query_start_loc_cpu[num_decodes : num_decodes + num_prefills + 1]
            )
            max_logits_bytes = envs.VLLM_SPARSE_INDEXER_MAX_LOGITS_MB * 1024 * 1024
            chunk_specs = split_indexer_prefill_chunks(
                common_attn_metadata.seq_lens_cpu[num_decodes:],
                prefill_query_lens_cpu,
                self.max_prefill_buffer_size,
                max_logits_bytes,
                request_offset=num_decodes,
            )
            chunks = [
                self.build_one_prefill_chunk(
                    req_slice,
                    query_slice,
                    query_start_loc_cpu,
                    common_attn_metadata.seq_lens_cpu,
                    common_attn_metadata.block_table_tensor,
                    skip_kv_gather=query_slice.start > 0,
                )
                for req_slice, query_slice in chunk_specs
            ]
            prefill_metadata = DeepseekV32IndexerPrefillMetadata(
                chunks=chunks,
            )

        decode_metadata = None
        if num_decodes > 0:
            torch.diff(
                common_attn_metadata.query_start_loc[: num_decodes + 1],
                out=self.decode_lens_buffer[:num_decodes],
            )
            decode_lens = self.decode_lens_buffer[:num_decodes]
            decode_lens_cpu = torch.diff(
                common_attn_metadata.query_start_loc_cpu[: num_decodes + 1]
            )

            seq_lens = common_attn_metadata.seq_lens[:num_decodes]
            block_table = common_attn_metadata.block_table_tensor[:num_decodes, ...]

            max_decode_len = int(decode_lens_cpu.max().item())
            next_n = 1 + self.num_speculative_tokens
            use_native = not self.use_flattening and max_decode_len == next_n

            seq_lens, block_table, decode_lens, batch_size, requires_padding = (
                self._prepare_decode_tensors(
                    seq_lens=seq_lens,
                    block_table=block_table,
                    decode_lens=decode_lens,
                    decode_lens_cpu=decode_lens_cpu,
                    query_start_loc=common_attn_metadata.query_start_loc[:num_decodes],
                    num_decodes=num_decodes,
                    num_decode_tokens=num_decode_tokens,
                    use_native=use_native,
                    next_n=next_n,
                    max_decode_len=max_decode_len,
                )
            )

            # DeepGEMM is required for the paged MQA logits on CUDA devices
            if current_platform.is_cuda() and has_deep_gemm():
                self.scheduler_metadata_buffer[:] = get_paged_mqa_logits_metadata(
                    seq_lens,
                    self.kv_cache_spec.block_size,
                    self.num_sms,
                )

            decode_metadata = DeepSeekV32IndexerDecodeMetadata(
                block_table=block_table,
                seq_lens=seq_lens,
                decode_lens=decode_lens,
                requires_padding=requires_padding,
                schedule_metadata=self.scheduler_metadata_buffer,
            )

        attn_metadata = DeepseekV32IndexerMetadata(
            seq_lens=common_attn_metadata.seq_lens,
            num_reqs=common_attn_metadata.num_reqs,
            max_query_len=common_attn_metadata.max_query_len,
            max_seq_len=common_attn_metadata.max_seq_len,
            num_actual_tokens=common_attn_metadata.num_actual_tokens,
            query_start_loc=common_attn_metadata.query_start_loc,
            slot_mapping=common_attn_metadata.slot_mapping,
            head_dim=128,
            num_decodes=num_decodes,
            num_decode_tokens=num_decode_tokens,
            num_prefills=num_prefills,
            num_prefill_tokens=num_prefill_tokens,
            prefill=prefill_metadata,
            decode=decode_metadata,
        )

        return attn_metadata