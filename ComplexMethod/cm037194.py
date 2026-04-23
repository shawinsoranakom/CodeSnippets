def __init__(
        self,
        kv_cache_spec: AttentionSpec,
        layer_names: list[str],
        vllm_config: VllmConfig,
        device: torch.device,
    ):
        super().__init__(kv_cache_spec, layer_names, vllm_config, device)
        self.cache_config = vllm_config.cache_config
        self.model_config = vllm_config.model_config
        self.attention_config = vllm_config.attention_config
        self._workspace_buffer = None
        self._prefill_wrapper: (
            BatchPrefillWithPagedKVCacheWrapper | BatchDCPPrefillWrapper | None
        ) = None  # Wrapper for prefill/append
        self._decode_wrapper = None  # Wrapper for decode (general shape)

        if envs.VLLM_BATCH_INVARIANT:
            self.decode_fixed_split_size = 2048
            self.prefill_fixed_split_size = 4096
            self.disable_split_kv = True
        else:
            self.decode_fixed_split_size = -1
            self.prefill_fixed_split_size = -1
            self.disable_split_kv = False

        self.compilation_config = vllm_config.compilation_config
        max_num_pages_per_req = cdiv(
            self.model_config.max_model_len, self.kv_cache_spec.block_size
        )
        max_num_reqs = vllm_config.scheduler_config.max_num_seqs
        max_num_pages = max_num_reqs * max_num_pages_per_req
        speculative_config = vllm_config.speculative_config
        num_spec_tokens = (
            speculative_config.num_speculative_tokens
            if speculative_config is not None
            else 0
        )
        self.enable_cuda_graph = (
            self.compilation_config.cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
        )
        if self.enable_cuda_graph:
            # For full cudagraph capture, one `decode_wrapper` for each batch
            # size is needed for FlashInfer.
            self._decode_wrappers_cudagraph: dict[
                int, BatchDecodeWithPagedKVCacheWrapper
            ] = {}
            self._decode_cudagraph_max_bs = (1 + num_spec_tokens) * max_num_reqs
            if self.compilation_config.max_cudagraph_capture_size is not None:
                self._decode_cudagraph_max_bs = min(
                    self._decode_cudagraph_max_bs,
                    self.compilation_config.max_cudagraph_capture_size,
                )
        try:
            self.dcp_world_size = get_dcp_group().world_size
            self.dcp_rank = get_dcp_group().rank_in_group
            self.dcp_kv_cache_interleave_size = (
                vllm_config.parallel_config.dcp_kv_cache_interleave_size
            )
        except AssertionError:
            # DCP might not be initialized in testing
            self.dcp_world_size = 1
            self.dcp_rank = 0
            self.dcp_kv_cache_interleave_size = 1
        self.use_dcp = self.dcp_world_size > 1
        self.dcp_a2a = (
            self.use_dcp and vllm_config.parallel_config.dcp_comm_backend == "a2a"
        )

        self.num_qo_heads = self.model_config.get_num_attention_heads(
            self.vllm_config.parallel_config
        )

        self.num_kv_heads = self.kv_cache_spec.num_kv_heads
        self.head_dim = self.kv_cache_spec.head_size
        self.page_size = self.kv_cache_spec.block_size

        if self.kv_cache_spec.kv_quant_mode != KVQuantMode.NONE:
            self.cache_dtype = self.cache_config.cache_dtype
            # Cannot use self.kv_cache_spec.dtype here because kv_cache_spec
            # storage dtype may not be the same as the op dtype (uint8 vs fp8_e4m3)
            self.is_kvcache_nvfp4 = self.cache_dtype == "nvfp4"
            if self.is_kvcache_nvfp4:
                # For NVFP4, kv_cache_dtype stays as the string "nvfp4"
                # which is passed to FlashInferImpl
                self.kv_cache_dtype = self.cache_dtype
                raise NotImplementedError("nvfp4 KV cache is not yet supported")
            else:
                self.kv_cache_dtype = FlashInferBackend.get_fp8_dtype_for_flashinfer(
                    self.cache_dtype
                )
        else:
            self.cache_dtype = "auto"
            self.is_kvcache_nvfp4 = False
            assert self.kv_cache_spec.dtype == self.model_config.dtype
            self.kv_cache_dtype = self.kv_cache_spec.dtype

        # Use model dtype as q dtype when TRTLLM attn is not supported, or
        # --attention-config.disable_flashinfer_q_quantization is set to 1. Otherwise,
        # try to use fp8 q if kv cache is fp8, and will fall back to model dtype
        # if TRTLLM attention kernel is not used when building attn metadata
        can_use_trtllm = can_use_trtllm_attention(self.num_qo_heads, self.num_kv_heads)

        if (
            can_use_trtllm
            and not vllm_config.attention_config.disable_flashinfer_q_quantization
        ):
            if self.is_kvcache_nvfp4:
                # NVFP4 KV cache uses FP8 quantized queries
                self.q_data_type = FlashInferBackend.get_fp8_dtype_for_flashinfer(
                    "fp8_e4m3"
                )
            else:
                self.q_data_type = self.kv_cache_dtype
        else:
            self.q_data_type = self.model_config.dtype

        # Prefer TRTLLM attention for decoding in all cases.
        # This allows us to use AttentionCGSupport.UNIFORM_BATCH mode.
        self.use_trtllm_decode_attention = can_use_trtllm
        self._init_reorder_batch_threshold(1, supports_spec_as_decode=can_use_trtllm)

        self._cascade_wrapper = None  # Wrapper for cascade attention

        # Global hyperparameters shared by all attention layers
        # TODO: discard this for trtllm-gen backend
        self.global_hyperparameters = infer_global_hyperparameters(
            get_per_layer_parameters(vllm_config, layer_names, FlashInferImpl)
        )
        self.sm_scale = self.global_hyperparameters.sm_scale
        self.window_left = self.global_hyperparameters.window_left
        self.logits_soft_cap = self.global_hyperparameters.logits_soft_cap
        self.has_sinks = self.global_hyperparameters.has_sinks
        if self.has_sinks and not can_use_trtllm:
            raise NotImplementedError(
                "FlashInfer backend currently does not support attention "
                "sinks, please use trtllm on blackwell or flash attention on "
                "earlier GPUs."
            )
        # Preparing persistent buffers
        # Since we do not have explicit synchronization in ModelRunnerV2, we do not pin
        # reused CPU buffers to avoid a race condition between step N async copies to
        # GPU and step N+1 buffer updates.
        self.pin_memory = (
            not envs.VLLM_USE_V2_MODEL_RUNNER and is_pin_memory_available()
        )
        self.paged_kv_indptr = self._make_buffer(max_num_reqs + 1)
        self.paged_kv_indptr_cpu_buffer = torch.zeros_like(
            self.paged_kv_indptr.cpu, pin_memory=self.pin_memory
        )  # Extra buffer for mutable paged_kv_indptr.cpu in cuda graph mode
        self.paged_kv_indices = self._make_buffer(max_num_pages)
        self.paged_kv_last_page_len = self._make_buffer(max_num_reqs)