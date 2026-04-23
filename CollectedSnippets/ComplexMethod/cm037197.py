def forward(
        self,
        layer: torch.nn.Module,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: torch.Tensor,
        attn_metadata: FlashInferMetadata,
        output: torch.Tensor,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass with FlashInfer.

        Args:
            query: shape = [num_tokens, num_heads, head_size]
            key: shape = [num_tokens, num_kv_heads, head_size]
            value: shape = [num_tokens, num_kv_heads, head_size]
            kv_cache: KV cache tensor with different possible shapes:
                - NHD: [num_blocks, 2, block_size, num_kv_heads, head_size]
                - HND: [num_blocks, 2, num_kv_heads, block_size, head_size]
            attn_metadata: Metadata for attention.
        Returns:
            shape = [num_tokens, num_heads * head_size]
        """
        if attn_metadata is None:
            # Profiling run.
            return output.fill_(0)

        # Ensure query dtype matches the expected dtype from attention metadata
        assert attn_metadata.q_data_type == query.dtype, (
            f"Query dtype mismatch: expected {attn_metadata.q_data_type}, "
            f"got {query.dtype}"
        )

        if self.bmm1_scale is None:
            self.bmm1_scale = self.scale
            if is_quantized_kv_cache(self.kv_cache_dtype):
                self.bmm1_scale *= layer._q_scale_float * layer._k_scale_float

        if self.bmm2_scale is None:
            self.bmm2_scale = 1.0
            if is_quantized_kv_cache(self.kv_cache_dtype):
                self.bmm2_scale *= layer._v_scale_float

        prefill_use_trtllm = isinstance(attn_metadata.prefill, TRTLLMPrefill)
        decode_use_trtllm = isinstance(attn_metadata.decode, TRTLLMDecode)

        # The attn+quant fusion happens when output_scale is provided.
        if output_scale is None:
            assert output_block_scale is None, (
                "output_block_scale is not supported when fusion has not happened"
            )
        else:
            assert attn_metadata.q_data_type == FP8_DTYPE, (
                "Query must be FP8 when attn+quant fusion happened."
            )
            assert (attn_metadata.num_prefills == 0 or prefill_use_trtllm) and (
                attn_metadata.num_decodes == 0 or decode_use_trtllm
            ), "Must use TRT-LLM attn"

            if output.dtype == FP8_DTYPE:
                assert output_block_scale is None, (
                    "output_block_scale should not be provided for fp8 output"
                )
            elif output.dtype == FP4_DTYPE:
                assert output_block_scale is not None, (
                    "output_block_scale is required for nvfp4 output"
                )
            else:
                raise ValueError(f"Unsupported output dtype: {output.dtype}")

            # TRTLLM attn kernel requires to scale to pass as a host scalar,
            # store the o scale as a host scalar in warmup run with cuda graph
            # not enabled
            if layer._o_scale_float is None:
                layer._o_scale_float = output_scale.cpu().item()
                if output.dtype == FP8_DTYPE:
                    self.bmm2_scale = self.bmm2_scale / layer._o_scale_float
                elif output.dtype == FP4_DTYPE:
                    self.o_sf_scale = layer._o_scale_float

        # IMPORTANT!
        # NOTE(woosuk): With piece-wise CUDA graphs, this method is executed in
        # eager-mode PyTorch. Thus, we need to be careful about any CPU overhead
        # in this method. For example, `view` and `slice` (or `[:n]`) operations
        # are surprisingly slow even in the case they do not invoke any GPU ops.
        # Minimize the PyTorch ops in this method as much as possible.
        # Whenever making a change in this method, please benchmark the
        # performance to make sure it does not introduce any overhead.

        num_actual_tokens = attn_metadata.num_actual_tokens

        # The FlashInfer api requires data to be in fp8_e4m3 or fp8_e5m2
        # to process the cache when the kv_cache_dtype is fp8
        if self.kv_sharing_target_layer_name is None and is_quantized_kv_cache(
            self.kv_cache_dtype
        ):
            torch_dtype = FlashInferBackend.get_fp8_dtype_for_flashinfer(
                self.kv_cache_dtype
            )
            kv_cache = kv_cache.view(torch_dtype)

        # Inputs and outputs may be padded for CUDA graphs
        query = query[:num_actual_tokens]
        key = key[:num_actual_tokens]
        value = value[:num_actual_tokens]
        output_padded = output
        output = output[:num_actual_tokens]

        if attn_metadata.use_cascade:
            # Cascade attention (rare case).
            assert attn_metadata.cascade_wrapper is not None
            output.copy_(attn_metadata.cascade_wrapper.run(query, kv_cache))
            return output

        # When using spec decoding, num_decodes can be < num_decode_tokens
        # because some decode requests may have more than one query token.
        num_decode_tokens = attn_metadata.num_decode_tokens
        num_prefill_tokens = attn_metadata.num_prefill_tokens

        stride_order = FlashInferBackend.get_kv_cache_stride_order()
        kv_cache_permute = kv_cache.permute(*stride_order)  # HND and contiguous

        # For NVFP4, the kv_cache last dim is full_dim (data + scale packed).
        # Split into correctly-strided data and scale views.
        nvfp4_kv_data = None
        nvfp4_kv_block_scales = None
        if self.is_kvcache_nvfp4:
            nvfp4_kv_data, nvfp4_kv_block_scales = nvfp4_kv_cache_split_views(
                kv_cache_permute
            )

        use_dcp = self.dcp_world_size > 1

        # Regular attention (common case).
        # Decodes are at the front and prefills are at the back.
        if num_prefill_tokens > 0:
            prefill_query = query[num_decode_tokens:]
            assert prefill_query.shape[0] == num_prefill_tokens

            if not prefill_use_trtllm:
                assert isinstance(attn_metadata.prefill, FIPrefill)
                prefill_wrapper = attn_metadata.prefill.wrapper
                assert prefill_wrapper is not None
                if use_dcp:
                    assert isinstance(prefill_wrapper, BatchDCPPrefillWrapper)
                    assert prefill_wrapper._context._window_left == self.window_left
                    assert prefill_wrapper._context._logits_soft_cap == (
                        self.logits_soft_cap or 0.0
                    )
                    assert prefill_wrapper._context._sm_scale == self.scale
                    assert not prefill_wrapper._context._causal
                    assert prefill_wrapper._new_tokens._window_left == self.window_left
                    assert prefill_wrapper._new_tokens._logits_soft_cap == (
                        self.logits_soft_cap or 0.0
                    )
                    assert prefill_wrapper._new_tokens._sm_scale == self.scale
                    assert prefill_wrapper._new_tokens._causal

                    prefill_wrapper.run(
                        layer,
                        prefill_query,
                        kv_cache_permute,
                        key[num_decode_tokens:],
                        value[num_decode_tokens:],
                        out=output[num_decode_tokens:],
                    )
                else:
                    assert isinstance(
                        prefill_wrapper, BatchPrefillWithPagedKVCacheWrapper
                    )
                    assert prefill_wrapper._window_left == self.window_left
                    assert prefill_wrapper._logits_soft_cap == (
                        self.logits_soft_cap or 0.0
                    )
                    assert prefill_wrapper._sm_scale == self.scale
                    assert prefill_wrapper._causal
                    prefill_wrapper.run(
                        prefill_query,
                        kv_cache_permute,
                        k_scale=layer._k_scale_float,
                        v_scale=layer._v_scale_float,
                        out=output[num_decode_tokens:],
                    )
            else:
                assert isinstance(attn_metadata.prefill, TRTLLMPrefill)
                # prefill_query may be non-contiguous or have degenerate strides
                # First ensure memory contiguity, then fix degenerate strides
                # with reshape. contiguous() alone doesn't fix degenerate
                # strides when a dimension has size 1.
                prefill_query = prefill_query.contiguous().reshape(prefill_query.shape)
                workspace_buffer = _get_trtllm_gen_workspace_buffer()
                block_tables_prefill = attn_metadata.prefill.block_tables
                seq_lens_prefill = attn_metadata.prefill.seq_lens

                # This path needs to be enabled with VLLM_KV_CACHE_LAYOUT = HND
                assert get_kv_cache_layout() == "HND"
                assert is_strictly_contiguous(prefill_query)
                assert is_strictly_contiguous(workspace_buffer)
                assert is_strictly_contiguous(block_tables_prefill)
                assert is_strictly_contiguous(seq_lens_prefill)

                if output.dtype == FP4_DTYPE:
                    assert self.o_sf_scale is not None
                    out = FP4Tensor(
                        data=output[num_decode_tokens:],
                        scale=output_block_scale,
                        scale_start_index=num_decode_tokens,
                        original_shape=prefill_query.shape,
                    )
                else:
                    assert self.o_sf_scale is None
                    out = output[num_decode_tokens:]

                prefill_kv_block_scales = None
                if self.is_kvcache_nvfp4:
                    # NVFP4 trtllm-gen kernel requires FP8 query.
                    assert attn_metadata.q_data_type == FP8_DTYPE, (
                        "NVFP4 KV cache requires FP8 quantized queries for "
                        "trtllm-gen prefill. Set "
                        "disable_flashinfer_q_quantization=False."
                    )
                    mock_kv_cache = nvfp4_kv_data
                    mock_block_table = block_tables_prefill
                    prefill_kv_block_scales = nvfp4_kv_block_scales  # noqa: F841
                elif (
                    attn_metadata.q_data_type != FP8_DTYPE
                    and self.kv_cache_dtype.startswith("fp8")
                ):
                    # TRTLLM prefill attention does not support BF16 Q
                    # and fp8 kv cache. So to enable prefill attention
                    # with fp8 kv cache, we can construct a mock block
                    # and mock kv cache with BF16 KV involved in the prefill
                    #
                    # The inner (block_size, head_size) dims must be
                    # contiguous; outer dims may have non-canonical strides
                    # (e.g. cross-layer unified allocation).
                    # Degenerate strides on outer dims break TMA descriptors
                    # (see flashinfer-ai/flashinfer#2232).
                    kv_strides = kv_cache_permute.stride()
                    assert (
                        kv_strides[-1] == 1
                        and kv_strides[-2] == kv_cache_permute.shape[-1]
                    ), (
                        "KV cache inner dims (block_size, head_size) must be "
                        f"contiguous, got strides {kv_strides}"
                    )
                    mock_kv_cache, mock_block_table = trtllm_prefill_attn_kvfp8_dequant(
                        kv_cache_permute,
                        block_tables_prefill,
                        layer._k_scale,
                        layer._v_scale,
                        attn_metadata.q_data_type,
                    )
                else:
                    mock_kv_cache = kv_cache_permute
                    mock_block_table = block_tables_prefill

                trtllm_batch_context_with_kv_cache(
                    query=prefill_query,
                    kv_cache=mock_kv_cache,
                    workspace_buffer=workspace_buffer,
                    block_tables=mock_block_table,
                    seq_lens=seq_lens_prefill,
                    max_q_len=attn_metadata.prefill.max_q_len,
                    max_kv_len=attn_metadata.prefill.max_seq_len,
                    bmm1_scale=self.bmm1_scale,
                    bmm2_scale=self.bmm2_scale,
                    batch_size=attn_metadata.num_prefills,
                    cum_seq_lens_q=attn_metadata.prefill.cum_seq_lens_q,
                    cum_seq_lens_kv=attn_metadata.prefill.cum_seq_lens_kv,
                    window_left=self.window_left,
                    sinks=self.sinks,
                    o_sf_scale=self.o_sf_scale,
                    out=out,
                )

        if num_decode_tokens > 0:
            decode_query = query[:num_decode_tokens]
            assert decode_query.shape[0] == num_decode_tokens

            if not decode_use_trtllm:
                assert isinstance(attn_metadata.decode, FIDecode)
                decode_wrapper = attn_metadata.decode.wrapper
                assert decode_wrapper is not None
                assert decode_wrapper._window_left == self.window_left
                assert decode_wrapper._logits_soft_cap == (self.logits_soft_cap or 0.0)
                assert decode_wrapper._sm_scale == self.scale

                if use_dcp:
                    decode_query = get_dcp_group().all_gather(
                        decode_query.contiguous(), dim=-2
                    )
                    output_tmp = torch.empty_like(decode_query)
                    lse = torch.empty(
                        (decode_query.size(0), decode_query.size(1)),
                        dtype=torch.float32,
                        device=decode_query.device,
                    )
                    decode_wrapper.run(
                        decode_query,
                        kv_cache_permute,
                        k_scale=layer._k_scale_float,
                        v_scale=layer._v_scale_float,
                        out=output_tmp,
                        lse=lse,
                        return_lse=True,
                    )
                    output[:num_decode_tokens] = self.dcp_combine(
                        output_tmp,
                        lse,
                        get_dcp_group(),
                    )
                else:
                    decode_wrapper.run(
                        decode_query,
                        kv_cache_permute,
                        k_scale=layer._k_scale_float,
                        v_scale=layer._v_scale_float,
                        out=output[:num_decode_tokens],
                    )
            else:
                # decode_query may be non-contiguous or have degenerate strides
                assert isinstance(attn_metadata.decode, TRTLLMDecode)
                # First ensure memory contiguity, then fix degenerate strides
                # with reshape. contiguous() alone doesn't fix degenerate
                # strides when a dimension has size 1.
                decode_query = decode_query.contiguous().reshape(decode_query.shape)
                workspace_buffer = _get_trtllm_gen_workspace_buffer()
                block_tables_decode = attn_metadata.decode.block_tables
                seq_lens_decode = attn_metadata.decode.seq_lens

                # This path needs to be enabled with VLLM_KV_CACHE_LAYOUT = HND
                assert get_kv_cache_layout() == "HND"
                assert is_strictly_contiguous(decode_query)
                assert is_strictly_contiguous(workspace_buffer)
                assert is_strictly_contiguous(block_tables_decode)
                assert is_strictly_contiguous(seq_lens_decode)
                # kv_cache outer dims may be non-contiguous (e.g.
                # cross-layer unified allocation), but inner dims
                # (block_size, head_size) must be contiguous and
                # strides must be canonical to avoid TMA descriptor
                # failures (see flashinfer-ai/flashinfer#2232).
                kv_strides = kv_cache_permute.stride()
                assert (
                    kv_strides[-1] == 1 and kv_strides[-2] == kv_cache_permute.shape[-1]
                ), (
                    "KV cache inner dims (block_size, head_size) must be "
                    f"contiguous, got strides {kv_strides}"
                )

                if output.dtype == FP4_DTYPE:
                    assert self.o_sf_scale is not None
                    out = FP4Tensor(
                        data=output[:num_decode_tokens],
                        scale=output_block_scale,
                        scale_start_index=0,
                        original_shape=decode_query.shape,
                    )
                else:
                    assert self.o_sf_scale is None
                    out = output[:num_decode_tokens]

                if num_decode_tokens % attn_metadata.num_decodes != 0:
                    # This gets triggered when the dummy_run forces
                    # attention to be initialized with q_len = 0
                    q_len_per_req = 1
                else:
                    q_len_per_req = num_decode_tokens // attn_metadata.num_decodes

                trtllm_batch_decode_with_kv_cache(
                    query=decode_query,
                    kv_cache=nvfp4_kv_data
                    if self.is_kvcache_nvfp4
                    else kv_cache_permute,
                    workspace_buffer=workspace_buffer,
                    block_tables=block_tables_decode,
                    seq_lens=seq_lens_decode,
                    max_seq_len=attn_metadata.decode.max_seq_len,
                    bmm1_scale=self.bmm1_scale,
                    bmm2_scale=self.bmm2_scale,
                    window_left=self.window_left,
                    sinks=self.sinks,
                    o_sf_scale=self.o_sf_scale,
                    out=out,
                    q_len_per_req=q_len_per_req,
                )
        return output_padded