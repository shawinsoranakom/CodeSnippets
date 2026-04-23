def build(
        self,
        common_prefix_len: int,
        common_attn_metadata: CommonAttentionMetadata,
        fast_build: bool = False,
    ) -> FlashInferMetadata:
        num_reqs = common_attn_metadata.num_reqs
        num_actual_tokens = common_attn_metadata.num_actual_tokens
        num_decodes, num_prefills, num_decode_tokens, num_prefill_tokens = (
            split_decodes_and_prefills(
                common_attn_metadata,
                decode_threshold=self.reorder_batch_threshold,
                require_uniform=True,
            )
        )

        page_size = self.page_size
        max_seq_len = common_attn_metadata.max_seq_len
        seq_lens = common_attn_metadata.seq_lens
        block_table_tensor = common_attn_metadata.block_table_tensor
        qo_indptr = common_attn_metadata.query_start_loc
        qo_indptr_cpu = common_attn_metadata.query_start_loc_cpu

        # Step 1: Decide which dispatch modes to use:
        # - Cascade attention (distinct mode)
        # - Prefill (FI native or TRTLLM)
        # - Decode (FI native or TRTLLM)
        use_cascade = common_prefix_len > 0
        uses_spec_reorder = self.reorder_batch_threshold > 1
        prefill_use_trtllm = use_trtllm_attention(
            self.num_qo_heads,
            self.num_kv_heads,
            num_prefill_tokens,
            max_seq_len,
            self.dcp_world_size,
            self.cache_dtype,
            self.q_data_type,
            is_prefill=True,
            force_use_trtllm=self.attention_config.use_trtllm_attention,
            has_sinks=self.has_sinks,
            has_spec=uses_spec_reorder,
        )
        decode_use_trtllm = (
            self.use_trtllm_decode_attention and self.dcp_world_size <= 1
        )

        all_uses_trtllm = (num_prefills == 0 or prefill_use_trtllm) and (
            num_decodes == 0 or decode_use_trtllm
        )

        if not all_uses_trtllm:
            if self.has_sinks:
                raise NotImplementedError(
                    "FlashInfer backend currently does not support attention "
                    "sinks, please use trtllm on blackwell or flash attention "
                    "on earlier GPUs."
                )

            if not self.global_hyperparameters.has_same_window_lefts:
                raise ValueError(
                    "Window left is not the same for all layers. "
                    "One potential fix is to set disable_sliding_window=True"
                )

            assert self.global_hyperparameters.has_same_all_params, (
                "FlashInfer backend currently only supports models in which "
                "all layers share the same values for the following "
                "hyperparameters: `window_left`, `logits_soft_cap`, "
                "`sm_scale`."
            )

            # The q quantization is not supported for non-trtllm attention,
            # fall back to model dtype.
            self.q_data_type = self.model_config.dtype

        # Step 2: Initialize the output metadata
        # Leave prefill/decode/cascade_wrapper empty, to be populated
        # case by case depending on the batch contents and backend selection.
        attn_metadata = FlashInferMetadata(
            num_actual_tokens=num_actual_tokens,
            slot_mapping=common_attn_metadata.slot_mapping,
            q_data_type=self.q_data_type,
            num_decodes=num_decodes,
            num_decode_tokens=num_decode_tokens,
            num_prefills=num_prefills,
            num_prefill_tokens=num_prefill_tokens,
            use_cascade=use_cascade,
            prefill=None,
            decode=None,
            cascade_wrapper=None,
        )

        # Guard access to seq_lens_cpu, which may not always be needed
        # and can be expensive to retrieve in async mode.
        # When all attention (both prefill and decode) uses TRTLLM,
        # seq_lens_cpu is not needed since TRTLLM paths use GPU tensors
        # (block_tables, seq_lens) directly.
        needs_seq_lens_cpu = self.use_dcp or use_cascade or not all_uses_trtllm
        seq_lens_cpu = common_attn_metadata.seq_lens_cpu if needs_seq_lens_cpu else None
        seq_lens_np = seq_lens_cpu.numpy() if seq_lens_cpu is not None else None
        num_blocks_np = (
            (seq_lens_np + (page_size - 1)) // page_size
            if seq_lens_np is not None
            else None
        )

        # Adjust seq_lens_cpu for DCP
        if self.use_dcp:
            assert seq_lens_cpu is not None
            if num_prefills > 0:
                qo_indptr_prefill_cpu = (
                    qo_indptr_cpu[num_decodes:] - qo_indptr_cpu[num_decodes]
                )
                query_lens_prefill_cpu = (
                    qo_indptr_prefill_cpu[1:] - qo_indptr_prefill_cpu[:-1]
                )
                seq_lens_cpu[num_decodes:] = (
                    seq_lens_cpu[num_decodes:] - query_lens_prefill_cpu
                )

            seq_lens_cpu = get_dcp_local_seq_lens(
                seq_lens_cpu,
                self.dcp_world_size,
                self.dcp_rank,
                self.dcp_kv_cache_interleave_size,
            )

        # Adjust num_block_np for cascade attention
        if use_cascade:
            assert num_blocks_np is not None
            assert common_prefix_len % page_size == 0
            num_common_kv_blocks = common_prefix_len // page_size
            num_blocks_np -= num_common_kv_blocks

        # Compute paged_kv_indices if necessary
        # paged_kv_indices is only needed for FlashInfer native paths;
        # TRTLLM paths use block_tables directly on GPU.
        needs_paged_kv_indices = use_cascade or not all_uses_trtllm
        if needs_paged_kv_indices:
            assert num_blocks_np is not None
            assert seq_lens_np is not None
            paged_kv_indices = self._compute_flashinfer_kv_metadata(
                num_blocks_np,
                seq_lens_np,
                block_table_tensor,
                num_reqs,
                page_size,
            )
        else:
            paged_kv_indices = None

        # Early-out for cascade attention
        if use_cascade:
            assert num_blocks_np is not None
            # Grab the blocks of the shared prefix from the first request.
            num_common_kv_blocks = common_prefix_len // page_size

            # Create CPU versions directly for cascade (no GPU versions needed)
            shared_qo_indptr_cpu = torch.tensor(
                [0, num_actual_tokens], dtype=torch.int32, device="cpu"
            )
            shared_kv_page_indptr_cpu = torch.tensor(
                [0, num_common_kv_blocks], dtype=torch.int32, device="cpu"
            )
            shared_kv_page_indices_cpu = block_table_tensor[0, :num_common_kv_blocks]
            shared_kv_last_page_len_cpu = torch.tensor(
                [page_size], dtype=torch.int32, device="cpu"
            )

            # Remove the blocks of the shared prefix from all requests.
            block_table_tensor = block_table_tensor[:, num_common_kv_blocks:]
            num_blocks_np -= num_common_kv_blocks

            assert paged_kv_indices is not None
            paged_kv_indptr_cpu = self.paged_kv_indptr.cpu[: 1 + num_reqs]
            paged_kv_last_page_len_cpu = self.paged_kv_last_page_len.cpu[:num_reqs]

            attn_metadata.cascade_wrapper = self._get_cascade_wrapper()
            attn_metadata.cascade_wrapper.plan(
                qo_indptr_arr=[shared_qo_indptr_cpu, qo_indptr_cpu],
                paged_kv_indptr_arr=[shared_kv_page_indptr_cpu, paged_kv_indptr_cpu],
                paged_kv_indices_arr=[shared_kv_page_indices_cpu, paged_kv_indices],
                paged_kv_last_page_len=[
                    shared_kv_last_page_len_cpu,
                    paged_kv_last_page_len_cpu,
                ],
                num_qo_heads=self.num_qo_heads,
                num_kv_heads=self.num_kv_heads,
                head_dim=self.head_dim,
                page_size=self.page_size,
                causal=True,
                sm_scale=self.sm_scale,
                window_left=self.window_left,
                logits_soft_cap=self.logits_soft_cap,
                q_data_type=self.q_data_type,
                kv_data_type=self.kv_cache_dtype,
            )
            return attn_metadata

        # Step 3: Handle prefill and decode pathways case by case
        ## PREFILL PATHWAY
        if num_prefills > 0:
            # Slices for shared prefill metadata
            prefill_start = num_decodes
            qo_indptr_prefill_cpu = (
                qo_indptr_cpu[prefill_start:] - qo_indptr_cpu[prefill_start]
            )
            assert qo_indptr_prefill_cpu.shape[0] == num_prefills + 1

            if prefill_use_trtllm:
                # Create GPU versions
                qo_indptr_prefill_gpu = (
                    qo_indptr[prefill_start:] - qo_indptr[prefill_start]
                )
                # Compute cum_seq_lens_kv on GPU to avoid CPU sync.
                # This is the cumulative sum of the number of KV cache
                # blocks per prefill request.
                prefill_seq_lens = seq_lens[prefill_start:]
                num_blocks_per_req = (prefill_seq_lens + page_size - 1) // page_size
                paged_kv_indptr_prefill_gpu = self.paged_kv_indptr.gpu[
                    prefill_start : num_reqs + 1
                ]
                paged_kv_indptr_prefill_gpu[0] = 0
                torch.cumsum(
                    num_blocks_per_req,
                    dim=0,
                    out=paged_kv_indptr_prefill_gpu[1:],
                )
                # Compute max_q_len for prefill requests
                query_lens_prefill_cpu = (
                    qo_indptr_prefill_cpu[1:] - qo_indptr_prefill_cpu[:-1]
                )
                max_q_len_prefill = int(query_lens_prefill_cpu.max().item())
                attn_metadata.prefill = TRTLLMPrefill(
                    block_tables=block_table_tensor[prefill_start:],
                    seq_lens=seq_lens[prefill_start:],
                    cum_seq_lens_q=qo_indptr_prefill_gpu,
                    cum_seq_lens_kv=paged_kv_indptr_prefill_gpu,
                    max_q_len=max_q_len_prefill,
                    max_seq_len=max_seq_len,
                )
            else:
                prefill_wrapper = self._get_prefill_wrapper()
                # Slicing CPU buffers that are only needed for FI native prefills
                paged_kv_last_page_len_prefill_cpu = self.paged_kv_last_page_len.cpu[
                    prefill_start:num_reqs
                ]
                assert paged_kv_last_page_len_prefill_cpu.shape[0] == num_prefills
                paged_kv_indptr_prefill_cpu = self.paged_kv_indptr.cpu[
                    prefill_start : num_reqs + 1
                ]
                assert paged_kv_indptr_prefill_cpu.shape[0] == num_prefills + 1
                if self.use_dcp:
                    assert isinstance(prefill_wrapper, BatchDCPPrefillWrapper)
                    prefill_wrapper.plan(
                        qo_indptr_cpu=qo_indptr_prefill_cpu,
                        paged_kv_indptr_cpu=paged_kv_indptr_prefill_cpu,
                        paged_kv_indices=paged_kv_indices,
                        paged_kv_last_page_len_cpu=paged_kv_last_page_len_prefill_cpu,
                        page_size=self.page_size,
                        num_qo_heads=self.num_qo_heads,
                        dcp_world_size=self.dcp_world_size,
                        num_kv_heads=self.num_kv_heads,
                        head_dim=self.head_dim,
                        sm_scale=self.sm_scale,
                        window_left=self.window_left,
                        logits_soft_cap=self.logits_soft_cap,
                        q_data_type=self.q_data_type,
                        kv_cache_dtype=self.kv_cache_dtype,
                        prefill_fixed_split_size=self.prefill_fixed_split_size,
                        disable_split_kv=self.disable_split_kv,
                    )
                else:
                    assert isinstance(
                        prefill_wrapper,
                        BatchPrefillWithPagedKVCacheWrapper,
                    )
                    prefill_wrapper.plan(
                        qo_indptr=qo_indptr_prefill_cpu,
                        paged_kv_indptr=paged_kv_indptr_prefill_cpu,
                        paged_kv_indices=paged_kv_indices,
                        paged_kv_last_page_len=paged_kv_last_page_len_prefill_cpu,
                        num_qo_heads=self.num_qo_heads,
                        num_kv_heads=self.num_kv_heads,
                        head_dim_qk=self.head_dim,
                        page_size=self.page_size,
                        causal=True,
                        sm_scale=self.sm_scale,
                        window_left=self.window_left,
                        logits_soft_cap=self.logits_soft_cap,
                        q_data_type=self.q_data_type,
                        kv_data_type=self.kv_cache_dtype,
                        o_data_type=self.model_config.dtype,
                        fixed_split_size=self.prefill_fixed_split_size,
                        disable_split_kv=self.disable_split_kv,
                    )
                attn_metadata.prefill = FIPrefill(wrapper=prefill_wrapper)

        ## DECODE PATHWAY
        if num_decodes > 0:
            if decode_use_trtllm:
                assert num_decode_tokens % num_decodes == 0, (
                    "TRTLLM decode requires uniform query lengths per request. "
                    f"Got {num_decode_tokens=} and {num_decodes=}."
                )
                attn_metadata.decode = TRTLLMDecode(
                    block_tables=block_table_tensor[:num_decodes],
                    seq_lens=seq_lens[:num_decodes],
                    max_seq_len=max_seq_len,
                )
            else:
                assert seq_lens_cpu is not None
                pure_decode = num_prefills == 0
                use_cudagraph = (
                    self.enable_cuda_graph
                    and pure_decode
                    and num_decode_tokens <= self._decode_cudagraph_max_bs
                )
                num_input_tokens = num_decode_tokens

                decode_wrapper = self._get_decode_wrapper(
                    num_input_tokens, use_cudagraph
                )
                # Use the persistent buffer with padding length,
                # instead of the same address but chunked version
                # in atten_metadata when using cudagraph.
                fast_plan_decode(
                    decode_wrapper,
                    indptr_cpu=self.paged_kv_indptr.cpu[: num_input_tokens + 1],
                    indices=paged_kv_indices,
                    last_page_len_cpu=self.paged_kv_last_page_len.cpu[
                        :num_input_tokens
                    ],
                    num_qo_heads=self.num_qo_heads * self.dcp_world_size,
                    num_kv_heads=self.num_kv_heads,
                    head_dim=self.head_dim,
                    page_size=self.page_size,
                    # Disable flashinfer's pos encoding and use vllm's rope.
                    pos_encoding_mode="NONE",
                    sm_scale=self.sm_scale,
                    window_left=self.window_left,
                    logits_soft_cap=self.logits_soft_cap,
                    q_data_type=self.q_data_type,
                    kv_data_type=self.kv_cache_dtype,
                    o_data_type=self.model_config.dtype,
                    fixed_split_size=self.decode_fixed_split_size,
                    disable_split_kv=self.disable_split_kv,
                )
                attn_metadata.decode = FIDecode(wrapper=decode_wrapper)
        return attn_metadata