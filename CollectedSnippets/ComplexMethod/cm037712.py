def __init__(
        self,
        kv_cache_spec: AttentionSpec,
        layer_names: list[str],
        vllm_config: VllmConfig,
        device: torch.device,
        metadata_cls: type[M] | None = None,
        supports_dcp_with_varlen: bool = False,
    ):
        self.metadata_cls = (
            metadata_cls if metadata_cls is not None else MLACommonMetadata
        )
        self.kv_cache_spec = kv_cache_spec
        scheduler_config = vllm_config.scheduler_config
        self.model_config = vllm_config.model_config
        parallel_config = vllm_config.parallel_config
        self.compilation_config = vllm_config.compilation_config
        self.vllm_config = vllm_config
        self.device = device

        self.num_heads = self.model_config.get_num_attention_heads(parallel_config)
        self.mla_dims = get_mla_dims(self.model_config)
        self.aot_schedule = current_platform.is_cuda()

        self.kv_cache_spec = kv_cache_spec
        self.q_data_type = self.determine_prefill_query_data_type(
            vllm_config, self.model_config.dtype
        )

        try:
            self.dcp_world_size = get_dcp_group().world_size
            self.dcp_rank = get_dcp_group().rank_in_group
        except AssertionError:
            # DCP might not be initialized in testing
            self.dcp_world_size = 1
            self.dcp_rank = 0
        self.dcp_local_block_size = parallel_config.cp_kv_cache_interleave_size
        self.dcp_virtual_block_size = self.dcp_local_block_size * self.dcp_world_size
        self.cp_kv_cache_interleave_size = parallel_config.cp_kv_cache_interleave_size

        # Don't try to access the runner on AMD
        if self.aot_schedule:
            self.page_size = self.kv_cache_spec.block_size

        self.chunked_prefill_workspace_size = (
            self.determine_chunked_prefill_workspace_size(vllm_config)
        )

        if self.dcp_world_size > 1:
            # Note(hc): The local kvcache is incomplete when DCP is triggered,
            # an additional kvcache allgather across the DCP group is therefore
            # required, so the workspace has to be enlarged by 1/DCP relative
            # to the original TP allocation.
            assert self.chunked_prefill_workspace_size % self.dcp_world_size == 0
            self.chunked_prefill_workspace = torch.empty(
                (
                    self.chunked_prefill_workspace_size
                    + self.chunked_prefill_workspace_size // self.dcp_world_size,
                    self.model_config.get_head_size(),
                ),
                dtype=self.model_config.dtype,
                device=device,
            )
        else:
            self.chunked_prefill_workspace = torch.empty(
                (
                    self.chunked_prefill_workspace_size,
                    self.model_config.get_head_size(),
                ),
                dtype=self.q_data_type,
                device=device,
            )

        self._use_cudnn_prefill = use_cudnn_prefill()
        self._use_fi_prefill = use_flashinfer_prefill()
        self._use_trtllm_ragged_prefill = use_trtllm_ragged_deepseek_prefill()
        self.prefill_metadata_cls = (
            FlashInferPrefillMetadata
            if self._use_fi_prefill
            else CudnnPrefillMetadata
            if self._use_cudnn_prefill
            else MLACommonPrefillMetadata
        )

        if self._use_fi_prefill:
            self._workspace_buffer = torch.empty(
                envs.VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE,
                dtype=torch.uint8,
                device=device,
            )

            self._fi_prefill_main: BatchPrefillWithRaggedKVCacheWrapper | None = None
            self._fi_prefill_chunks: list[BatchPrefillWithRaggedKVCacheWrapper] = []

            self._global_hyperparameters = infer_global_hyperparameters(
                get_per_layer_parameters(vllm_config, layer_names, MLACommonImpl)  # type: ignore[type-abstract]
            )

        if self._use_trtllm_ragged_prefill:
            self._workspace_buffer = torch.empty(
                envs.VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE,
                dtype=torch.uint8,
                device=device,
            )

        if self._use_cudnn_prefill:
            self.cudnn_workspace = torch.empty(
                CUDNN_WORKSPACE_SIZE * scheduler_config.max_num_seqs,
                dtype=torch.int8,
                device=device,
            )

        supports_spec_decode = self.query_len_support != QueryLenSupport.SINGLE_ONLY
        self._init_reorder_batch_threshold(
            self.reorder_batch_threshold, supports_spec_decode, supports_dcp_with_varlen
        )

        # Validate consistency between query_len_support and reorder_batch_threshold
        if self.query_len_support == QueryLenSupport.SINGLE_ONLY:
            assert self.reorder_batch_threshold == 1, (
                f"reorder_batch_threshold must be 1 when query_len_support is "
                f"SINGLE_ONLY, got {self.reorder_batch_threshold}"
            )