def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: CommonAttentionMetadata,
        fast_build: bool = False,
    ) -> M:
        num_reqs = common_attn_metadata.num_reqs
        num_tokens = common_attn_metadata.num_actual_tokens
        max_query_len = common_attn_metadata.max_query_len
        max_seq_len = common_attn_metadata.max_seq_len

        # Note(simon): be careful about the CPU <> GPU memory movement in this
        # function. We should avoid GPU -> CPU sync as much as possible because
        # it blocks on all previous kernels.
        device = self.device
        block_table_tensor = common_attn_metadata.block_table_tensor
        slot_mapping = common_attn_metadata.slot_mapping

        query_start_loc = common_attn_metadata.query_start_loc
        query_start_loc_cpu = common_attn_metadata.query_start_loc_cpu
        seq_lens = common_attn_metadata.seq_lens
        dcp_local_seq_lens = common_attn_metadata.dcp_local_seq_lens

        num_decodes, num_prefills, num_decode_tokens, num_prefill_tokens = (
            split_decodes_and_prefills(
                common_attn_metadata,
                decode_threshold=self.reorder_batch_threshold,
                require_uniform=(self.query_len_support != QueryLenSupport.VARLEN),
            )
        )

        assert num_decodes + num_prefills == num_reqs
        assert num_decode_tokens + num_prefill_tokens == num_tokens

        prefill_metadata = None
        if num_prefills > 0:
            num_computed_tokens_cpu = (
                common_attn_metadata.compute_num_computed_tokens().cpu()
            )

            reqs_start = num_decodes  # prefill_start

            context_lens_cpu = num_computed_tokens_cpu[reqs_start:num_reqs]
            max_context_len_cpu = context_lens_cpu.max().item()
            num_prefills_with_context_cpu = (context_lens_cpu > 0).sum().item()
            prefill_query_start_loc = (
                query_start_loc[reqs_start:] - query_start_loc[reqs_start]
            )
            prefill_query_start_loc_cpu = (
                query_start_loc_cpu[reqs_start:] - query_start_loc_cpu[reqs_start]
            )

            chunked_context_metadata = None
            if max_context_len_cpu > 0:
                # NOTE: it is recommend you read the `Chunked Prefill` section
                # in the comment at the top of the file before trying to
                # understand the following code

                # currently we allocate an equal amount of workspace for each
                # prefill in the batch, we could probably use a more advanced
                # algorithm here and allocate more workspace to prefills with
                # longer context lengths
                max_context_chunk = (
                    self.chunked_prefill_workspace_size // num_prefills_with_context_cpu
                )

                if self.aot_schedule:
                    # align max_context_chunk to page_size by rounding down,
                    # currently the `gather_and_maybe_dequant_cache` kernel
                    # cannot handle `context_chunk_starts` that are not aligned
                    # to page_size
                    max_context_chunk = round_down(max_context_chunk, self.page_size)

                assert max_context_chunk > 0
                num_chunks = cdiv(max_context_len_cpu, max_context_chunk)

                # if `max_context_chunk = 256`, `num_chunks = 3`, and
                #   `num_prefills_with_context = 4`, create a tensor that looks
                # like
                #  [[0, 0, 0, 0], [256, 256, 256, 256], [512, 512, 512, 512]]
                # Note(simon): this is done in CPU because of downstream's
                # of `to_list`.
                chunk_starts = (
                    torch.arange(num_chunks, dtype=torch.int32)
                    .unsqueeze(1)
                    .expand(-1, num_prefills)
                    * max_context_chunk
                )
                chunk_ends = torch.min(
                    context_lens_cpu.unsqueeze(0), chunk_starts + max_context_chunk
                )
                chunk_seq_lens = (chunk_ends - chunk_starts).clamp(min=0)

                cu_seq_lens_cpu = torch.zeros(
                    num_chunks, num_prefills + 1, dtype=torch.int32, pin_memory=True
                )
                torch.cumsum(
                    chunk_seq_lens, dim=1, out=cu_seq_lens_cpu[:, 1:], dtype=torch.int32
                )
                chunk_total_token = cu_seq_lens_cpu[:, -1]

                max_token_num_over_chunk = chunk_total_token.max().item()
                token_to_seq_tensor_cpu = torch.zeros(
                    [num_chunks, max_token_num_over_chunk], dtype=torch.int32
                )
                range_idx = torch.arange(num_prefills, dtype=torch.int32)
                for i in range(num_chunks):
                    chunk_token_to_seq_tensor = torch.repeat_interleave(
                        range_idx, chunk_seq_lens[i]
                    )
                    chunk_len = chunk_token_to_seq_tensor.shape[0]
                    token_to_seq_tensor_cpu[i, :chunk_len] = chunk_token_to_seq_tensor

                if self.dcp_world_size > 1:
                    local_context_lens_allranks = get_dcp_local_seq_lens(
                        context_lens_cpu,
                        self.dcp_world_size,
                        None,
                        self.dcp_local_block_size,
                    )
                    # Note(qcs): The max local context lengths
                    # padded to `dcp_local_block_size`.
                    padded_local_context_lens_cpu: torch.Tensor = (
                        cdiv(
                            context_lens_cpu,
                            self.dcp_virtual_block_size,
                        )
                        * self.dcp_local_block_size
                    )
                    # Note(hc): The above max_context_chunk already enforces
                    # block_size alignment, DCP just need the block_size can
                    # be divisible by dcp_world_size, because DCP use
                    # cp_gather_cache which not require `cp_chunk_starts`
                    # aligned to page_size.
                    assert max_context_chunk % self.dcp_world_size == 0
                    padded_local_max_context_chunk_across_ranks = (
                        cdiv(
                            max_context_chunk,
                            self.dcp_virtual_block_size,
                        )
                        * self.dcp_local_block_size
                    )
                    local_chunk_starts = (
                        torch.arange(num_chunks, dtype=torch.int32)
                        .unsqueeze(1)
                        .expand(-1, num_prefills)
                        * padded_local_max_context_chunk_across_ranks
                    )
                    local_chunk_ends = torch.min(
                        padded_local_context_lens_cpu.unsqueeze(0),
                        local_chunk_starts
                        + padded_local_max_context_chunk_across_ranks,
                    )
                    padded_local_chunk_seq_lens = (
                        local_chunk_ends - local_chunk_starts
                    ).clamp(min=0)

                    padded_local_cu_chunk_seq_lens_cpu = torch.zeros(
                        num_chunks, num_prefills + 1, dtype=torch.int32, pin_memory=True
                    )
                    torch.cumsum(
                        padded_local_chunk_seq_lens,
                        dim=1,
                        out=padded_local_cu_chunk_seq_lens_cpu[:, 1:],
                        dtype=torch.int32,
                    )

                chunked_context_metadata_cls = (
                    CudnnPrefillMetadata.ChunkedContextMetadata
                    if self._use_cudnn_prefill
                    else MLACommonPrefillMetadata.ChunkedContextMetadata
                )
                prefill_tokens_with_context = None
                if num_prefills_with_context_cpu > 0:
                    prefill_tokens_with_context = prefill_query_start_loc_cpu[
                        num_prefills_with_context_cpu
                    ].item()
                if self.dcp_world_size > 1:
                    chunked_context_metadata = chunked_context_metadata_cls(
                        cu_seq_lens=cu_seq_lens_cpu.to(device, non_blocking=True),
                        starts=local_chunk_starts.to(device, non_blocking=True),
                        seq_tot=padded_local_chunk_seq_lens.sum(dim=1).tolist(),
                        max_seq_lens=chunk_seq_lens.max(dim=1).values.tolist(),
                        seq_lens=chunk_seq_lens,
                        token_to_seq=token_to_seq_tensor_cpu.to(
                            device, non_blocking=True
                        ),
                        chunk_total_token=chunk_total_token.tolist(),
                        workspace=self.chunked_prefill_workspace,
                        padded_local_chunk_seq_lens=padded_local_chunk_seq_lens.tolist(),
                        local_context_lens_allranks=local_context_lens_allranks.tolist(),
                        padded_local_cu_seq_lens=padded_local_cu_chunk_seq_lens_cpu.to(
                            device, non_blocking=True
                        ),
                        cu_seq_lens_lst=cu_seq_lens_cpu.tolist(),
                        chunk_size=padded_local_max_context_chunk_across_ranks,
                        prefill_tokens_with_context=prefill_tokens_with_context,
                    )
                else:
                    chunked_context_metadata = chunked_context_metadata_cls(
                        cu_seq_lens=cu_seq_lens_cpu.to(device, non_blocking=True),
                        starts=chunk_starts.to(device, non_blocking=True),
                        seq_tot=chunk_seq_lens.sum(dim=1).tolist(),
                        max_seq_lens=chunk_seq_lens.max(dim=1).values.tolist(),
                        seq_lens=chunk_seq_lens,
                        token_to_seq=token_to_seq_tensor_cpu.to(
                            device, non_blocking=True
                        ),
                        chunk_total_token=chunk_total_token,
                        workspace=self.chunked_prefill_workspace,
                        prefill_tokens_with_context=prefill_tokens_with_context,
                    )

                if self._use_cudnn_prefill:
                    chunked_context_metadata.seq_lens = chunk_seq_lens

                assert (
                    max(chunked_context_metadata.max_seq_lens)
                    <= self.chunked_prefill_workspace_size
                )

            prefill_metadata = self.prefill_metadata_cls(
                block_table=block_table_tensor[reqs_start:, ...],
                query_start_loc=prefill_query_start_loc,
                max_query_len=max_query_len,
                chunked_context=chunked_context_metadata,
                output_dtype=self.model_config.dtype,
                q_data_type=self.q_data_type,
            )

            if self._use_cudnn_prefill:
                assert isinstance(prefill_metadata, CudnnPrefillMetadata)
                prefill_metadata.query_seq_lens = (
                    prefill_query_start_loc[1:] - prefill_query_start_loc[:-1]
                )
                prefill_metadata.cudnn_workspace = self.cudnn_workspace

            if self._use_trtllm_ragged_prefill:
                prefill_metadata.query_seq_lens = (
                    prefill_query_start_loc[1:] - prefill_query_start_loc[:-1]
                )
                prefill_metadata.workspace_buffer = self._workspace_buffer

        decode_metadata = None
        if num_decodes > 0:
            dcp_tot_seq_lens_device = None
            if self.dcp_world_size > 1:
                dcp_tot_seq_lens_device = seq_lens[:num_decodes]
                seq_lens = dcp_local_seq_lens

                # After DCP distribution, the maximum number of tokens for any rank is
                # ceil(L / (N * I)) * I, where L is max_seq_len, N is dcp_world_size,
                # and I is cp_kv_cache_interleave_size.
                # This eliminates GPU->CPU sync while minimizing workspace
                # over-allocation.
                num_partitions = self.dcp_world_size * self.cp_kv_cache_interleave_size
                max_seq_len = (
                    (max_seq_len + num_partitions - 1) // num_partitions
                ) * self.cp_kv_cache_interleave_size

            decode_metadata = self._build_decode(
                block_table_tensor=block_table_tensor[:num_decodes, ...],
                seq_lens_device=seq_lens[:num_decodes],
                max_seq_len=max_seq_len,
                query_start_loc_cpu=query_start_loc_cpu[: num_decodes + 1],
                query_start_loc_device=query_start_loc[: num_decodes + 1],
                num_decode_tokens=num_decode_tokens,
                dcp_tot_seq_lens_device=dcp_tot_seq_lens_device,
            )

        attn_metadata = self.metadata_cls(
            num_reqs=common_attn_metadata.num_reqs,
            max_query_len=common_attn_metadata.max_query_len,
            max_seq_len=max_seq_len,
            num_actual_tokens=num_tokens,
            query_start_loc=query_start_loc,
            slot_mapping=slot_mapping,
            head_dim=self.model_config.get_head_size(),
            # MLACommonMetadata Chunk prefill specific
            num_decodes=num_decodes,
            num_decode_tokens=num_decode_tokens,
            num_prefills=num_prefills,
            prefill=prefill_metadata,
            decode=decode_metadata,
        )

        if self._use_fi_prefill and num_prefills > 0:
            assert isinstance(attn_metadata.prefill, FlashInferPrefillMetadata)
            self._build_fi_prefill_wrappers(attn_metadata.prefill)

        return attn_metadata