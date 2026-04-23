def __init__(
        self,
        vllm_config: VllmConfig,
        device: torch.device,
    ):
        self.vllm_config = vllm_config
        self.model_config = vllm_config.model_config
        self.cache_config = vllm_config.cache_config
        self.offload_config = vllm_config.offload_config
        self.compilation_config = vllm_config.compilation_config
        self.lora_config = vllm_config.lora_config
        self.load_config = vllm_config.load_config
        self.parallel_config = vllm_config.parallel_config
        self.scheduler_config = vllm_config.scheduler_config
        self.speculative_config = vllm_config.speculative_config
        self.observability_config = vllm_config.observability_config

        model_config = self.model_config
        cache_config = self.cache_config
        scheduler_config = self.scheduler_config
        parallel_config = self.parallel_config
        self.device = device
        self.pin_memory = is_pin_memory_available()
        self.dtype = self.model_config.dtype

        self.kv_cache_dtype = kv_cache_dtype_str_to_dtype(
            cache_config.cache_dtype, self.model_config
        )

        self.is_pooling_model = model_config.runner_type == "pooling"
        self.enable_prompt_embeds = model_config.enable_prompt_embeds
        self.is_multimodal_raw_input_only_model = (
            model_config.is_multimodal_raw_input_only_model
        )
        # These will be overridden in load_model()
        self.is_multimodal_pruning_enabled = False
        self.requires_sequential_video_encoding = False
        # Set to True after init_routed_experts_capturer() completes.
        # Prevents routed experts code from running during profiling/dummy run.
        self.routed_experts_initialized = False
        self.max_model_len = model_config.max_model_len

        # Always set to false after the first forward pass
        self.calculate_kv_scales = self.cache_config.calculate_kv_scales
        self.dcp_world_size = self.parallel_config.decode_context_parallel_size
        self.dcp_rank = 0 if self.dcp_world_size <= 1 else get_dcp_group().rank_in_group
        self.max_num_tokens = scheduler_config.max_num_batched_tokens
        self.max_num_reqs = scheduler_config.max_num_seqs

        # Broadcast PP output for external_launcher (torchrun)
        # to make sure we are synced across pp ranks
        # TODO: Support overlapping micro-batches
        # https://github.com/vllm-project/vllm/issues/18019
        self.broadcast_pp_output = (
            self.parallel_config.distributed_executor_backend == "external_launcher"
            and len(get_pp_group().ranks) > 1
        )

        # Model-related.
        self.num_query_heads = model_config.get_num_attention_heads(parallel_config)
        self.inputs_embeds_size = model_config.get_inputs_embeds_size()
        # Only relevant for models using ALiBi (e.g, MPT)
        self.use_alibi = model_config.uses_alibi

        self.cascade_attn_enabled = not self.model_config.disable_cascade_attn
        self.is_mm_prefix_lm = self.model_config.is_mm_prefix_lm

        # Multi-modal data support
        self.mm_registry = MULTIMODAL_REGISTRY
        self.uses_mrope = model_config.uses_mrope
        self.uses_xdrope_dim = model_config.uses_xdrope_dim
        self.supports_mm_inputs = self.mm_registry.supports_multimodal_inputs(
            model_config
        )

        if self.model_config.is_encoder_decoder:
            # Maximum length of the encoder input, only for encoder-decoder
            # models.
            self.max_encoder_len = scheduler_config.max_num_encoder_input_tokens
        else:
            self.max_encoder_len = 0

        # Async scheduling
        self.use_async_scheduling = self.scheduler_config.async_scheduling

        # Sampler
        self.sampler = Sampler(logprobs_mode=self.model_config.logprobs_mode)

        self.eplb_state: EplbState | None = None
        # NOTE(yongji): flag to temporarily disable EPLB during scaling up/down
        self.eep_eplb_suppressed = False
        """
        State of the expert parallelism load balancer.

        Will be lazily initialized when the model is loaded.
        """

        # Lazy initializations
        # self.model: nn.Module  # Set after load_model
        # Initialize in initialize_kv_cache
        self.kv_caches: list[torch.Tensor] = []
        # Initialize in initialize_kv_cache_tensors
        self.cross_layers_kv_cache: torch.Tensor | None = None
        self.cross_layers_attn_backend: type[AttentionBackend] | None = None
        # indexes: [kv_cache_group_id][attn_group]
        self.attn_groups: list[list[AttentionGroup]] = []
        # self.kv_cache_config: KVCacheConfig

        # mm_hash ->  encoder_output
        self.encoder_cache: dict[str, torch.Tensor] = {}
        self.late_interaction_runner = LateInteractionRunner()

        # Encoder CUDA graph manager (initialized after model load if enabled)
        self.encoder_cudagraph_manager: EncoderCudaGraphManager | None = None

        self.use_aux_hidden_state_outputs = False
        # Set up speculative decoding.
        # NOTE(Jiayi): currently we put the entire draft model on
        # the last PP rank. This is not ideal if there are many
        # layers in the draft model.
        if self.speculative_config and get_pp_group().is_last_rank:
            self.drafter: (
                NgramProposer  # noqa: F823
                | NgramProposerGPU
                | SuffixDecodingProposer
                | EagleProposer
                | DFlashProposer
                | DraftModelProposer
                | MedusaProposer
                | ExtractHiddenStatesProposer
            )
            if self.speculative_config.method == "ngram":
                from vllm.v1.spec_decode.ngram_proposer import NgramProposer

                self.drafter = NgramProposer(self.vllm_config)
            elif self.speculative_config.uses_draft_model():
                self.drafter = DraftModelProposer(
                    vllm_config=self.vllm_config,
                    device=self.device,
                    runner=self,
                )
            elif self.speculative_config.use_ngram_gpu():
                self.drafter = NgramProposerGPU(self.vllm_config, self.device, self)
                self.num_tokens_no_spec_gpu = torch.zeros(
                    self.max_num_reqs, dtype=torch.int32, device=device
                )
                self.token_ids_gpu_tensor = torch.zeros(
                    self.max_num_reqs,
                    self.max_model_len,
                    dtype=torch.int32,
                    device=device,
                )
                self._ngram_pinned_idx_buf = torch.zeros(
                    self.max_num_reqs, dtype=torch.long, pin_memory=True
                )
                self._ngram_pinned_val_buf = torch.zeros(
                    self.max_num_reqs, dtype=torch.int32, pin_memory=True
                )
            elif self.speculative_config.use_dflash():
                self.drafter = DFlashProposer(self.vllm_config, self.device, self)
                self.use_aux_hidden_state_outputs = True
            elif self.speculative_config.method == "suffix":
                self.drafter = SuffixDecodingProposer(self.vllm_config)
            elif self.speculative_config.use_eagle():
                self.drafter = EagleProposer(self.vllm_config, self.device, self)
                if self.speculative_config.method == "eagle3":
                    self.use_aux_hidden_state_outputs = (
                        self.drafter.eagle3_use_aux_hidden_state
                    )
            elif self.speculative_config.method == "medusa":
                self.drafter = MedusaProposer(
                    vllm_config=self.vllm_config, device=self.device
                )
            elif self.speculative_config.method == "extract_hidden_states":
                self.drafter = ExtractHiddenStatesProposer(
                    vllm_config=self.vllm_config, device=self.device
                )
                self.use_aux_hidden_state_outputs = True
            else:
                raise ValueError(
                    "Unknown speculative decoding method: "
                    f"{self.speculative_config.method}"
                )
            self.rejection_sampler = RejectionSampler(self.sampler)

        self.num_spec_tokens = 0
        self.valid_sampled_token_count_gpu: torch.Tensor | None = None
        if self.speculative_config:
            self.num_spec_tokens = self.speculative_config.num_speculative_tokens
            draft_config = self.speculative_config.draft_model_config
            if draft_config is not None and draft_config.max_model_len is not None:
                self.effective_drafter_max_model_len = draft_config.max_model_len
            else:
                self.effective_drafter_max_model_len = self.max_model_len
        self.use_async_spec_decode = (
            self.use_async_scheduling and self.num_spec_tokens > 0
        )

        # Request states.
        self.requests: dict[str, CachedRequestState] = {}
        # NOTE(rob): num_prompt_logprobs only includes reqs
        # that are currently in the prefill phase.
        self.num_prompt_logprobs: dict[str, int] = {}

        # Input Batch
        # NOTE(Chen): Ideally, we should initialize the input batch inside
        # `initialize_kv_cache` based on the kv cache config. However, as in
        # https://github.com/vllm-project/vllm/pull/18298, due to some unknown
        # reasons, we have to initialize the input batch before `load_model`,
        # quantization + weight offloading will fail otherwise. As a temporary
        # solution, we initialize the input batch here, and re-initialize it
        # in `initialize_kv_cache` if the block_sizes here is different from
        # the block_sizes in the kv cache config.
        logits_processors = model_config.logits_processors
        custom_logitsprocs: Sequence[str | type[LogitsProcessor]] = (
            tuple(logits_processors) if logits_processors is not None else ()
        )
        placeholder_block_size = (
            self.cache_config.block_size or CacheConfig.DEFAULT_BLOCK_SIZE
        )
        self._init_block_sizes = [placeholder_block_size]
        self._init_kernel_block_sizes = [placeholder_block_size]
        self.input_batch = InputBatch(
            max_num_reqs=self.max_num_reqs,
            # We need to use the encoder length for encoder-decoder
            # because of KV cache for cross-attention.
            max_model_len=max(self.max_model_len, self.max_encoder_len),
            max_num_batched_tokens=self.max_num_tokens,
            device=self.device,
            pin_memory=self.pin_memory,
            vocab_size=self.model_config.get_vocab_size(),
            block_sizes=[placeholder_block_size],
            kernel_block_sizes=[placeholder_block_size],
            is_spec_decode=bool(self.vllm_config.speculative_config),
            logitsprocs=build_logitsprocs(
                self.vllm_config,
                self.device,
                self.pin_memory,
                self.is_pooling_model,
                custom_logitsprocs,
            ),
            # We currently don't know whether a particular custom logits processor
            # uses output token ids so we set this conservatively.
            # ThinkingTokenBudgetLogitsProcessor also needs output token ids to
            # correctly track think start/end token sequences in async scheduling.
            logitsprocs_need_output_token_ids=bool(custom_logitsprocs)
            or self.vllm_config.reasoning_config is not None,
            is_pooling_model=self.is_pooling_model,
            cp_kv_cache_interleave_size=self.parallel_config.cp_kv_cache_interleave_size,
        )

        # Separate cuda stream for overlapping transfer of sampled token ids from
        # GPU to CPU when async scheduling is enabled.
        self.async_output_copy_stream: torch.cuda.Stream | None = None
        # cuda event to synchronize use of reused CPU tensors between steps
        # when async scheduling is enabled.
        self.prepare_inputs_event: torch.Event | None = None
        if self.use_async_scheduling:
            self.async_output_copy_stream = torch.cuda.Stream()
            self.prepare_inputs_event = torch.Event()

        # self.cudagraph_batch_sizes sorts in ascending order.
        if (
            self.compilation_config.cudagraph_capture_sizes
            and self.compilation_config.cudagraph_mode != CUDAGraphMode.NONE
        ):
            self.cudagraph_batch_sizes = sorted(
                self.compilation_config.cudagraph_capture_sizes
            )
        else:
            self.cudagraph_batch_sizes = []

        # Cache the device properties.
        self._init_device_properties()

        # Encoder timing registry for observability
        self.encoder_timing_registry: dict[str, EncoderTimingStats] = {}
        self._encoder_timing_lock = threading.Lock()

        # Persistent buffers for CUDA graphs.
        self.input_ids = self._make_buffer(self.max_num_tokens, dtype=torch.int32)
        self.positions = torch.zeros(
            self.max_num_tokens, dtype=torch.int64, device=self.device
        )
        self.query_start_loc = self._make_buffer(
            self.max_num_reqs + 1, dtype=torch.int32
        )
        self.seq_lens = torch.zeros(
            self.max_num_reqs, dtype=torch.int32, device=self.device
        )
        self.optimistic_seq_lens_cpu = torch.zeros(
            self.max_num_reqs, dtype=torch.int32, pin_memory=self.pin_memory
        )
        self.num_computed_tokens = torch.zeros(
            self.max_num_reqs, dtype=torch.int32, device=self.device
        )
        self.prev_num_draft_tokens = self._make_buffer(
            self.max_num_reqs, dtype=torch.int32
        )
        self.req_indices = self._make_buffer(self.max_num_tokens, dtype=torch.int64)
        # Maps current batch position -> previous batch position (-1 for new reqs)
        self.prev_positions = self._make_buffer(self.max_num_reqs, dtype=torch.int64)
        self.num_scheduled_tokens = self._make_buffer(
            self.max_num_reqs, dtype=torch.int32
        )

        self.encoder_seq_lens = self._make_buffer(self.max_num_reqs, dtype=torch.int32)
        if self.dcp_world_size > 1:
            self.dcp_local_seq_lens = self._make_buffer(
                self.max_num_reqs, dtype=torch.int32
            )
        # Because inputs_embeds may be bfloat16 and we don't need a numpy
        # version of this tensor, avoid a RuntimeError by not creating a
        # numpy buffer.
        self.inputs_embeds = self._make_buffer(
            self.max_num_tokens, self.inputs_embeds_size, dtype=self.dtype, numpy=False
        )
        self.is_token_ids = self._make_buffer(self.max_num_tokens, dtype=torch.bool)
        self.discard_request_mask = self._make_buffer(
            self.max_num_reqs, dtype=torch.bool
        )
        self.num_decode_draft_tokens = self._make_buffer(
            self.max_num_reqs, dtype=torch.int32
        )
        self.num_accepted_tokens = self._make_buffer(
            self.max_num_reqs, dtype=torch.int32
        )

        # Only relevant for models using M-RoPE (e.g, Qwen2-VL)
        if self.uses_mrope:
            # NOTE: `mrope_positions` is implemented with one additional dummy
            # position on purpose to make it non-contiguous so that it can work
            # with torch compile.
            # See detailed explanation in https://github.com/vllm-project/vllm/pull/12128#discussion_r1926431923

            # NOTE: When M-RoPE is enabled, position ids are 3D regardless of
            # the modality of inputs. For text-only inputs, each dimension has
            # identical position IDs, making M-RoPE functionally equivalent to
            # 1D-RoPE.
            # See page 5 of https://arxiv.org/abs/2409.12191
            self.mrope_positions = self._make_buffer(
                (3, self.max_num_tokens + 1), dtype=torch.int64
            )

        # Only relevant for models using XD-RoPE (e.g, HunYuan-VL)
        if self.uses_xdrope_dim > 0:
            # Similar to mrope but use assigned dimension number for RoPE, 4 as default.
            self.xdrope_positions = self._make_buffer(
                (self.uses_xdrope_dim, self.max_num_tokens + 1), dtype=torch.int64
            )

        # None in the first PP rank. The rest are set after load_model.
        self.intermediate_tensors: IntermediateTensors | None = None

        # OPTIMIZATION: Cache the arange tensors rather than creating them
        # every step. Keep in int64 to avoid overflow with long context.
        # - arange_np: immutable [0, 1, 2, ...] used as source for batched computation
        # - query_pos: CpuGpuBuffer for the computed batched arange result
        arange_size = max(self.max_num_reqs + 1, self.max_num_tokens)
        self.arange_np = np.arange(arange_size, dtype=np.int64)
        self.query_pos = self._make_buffer(arange_size, dtype=torch.int64)
        self._arange_scratch = np.empty(arange_size, dtype=np.int64)

        # Layer pairings for cross-layer KV sharing.
        # If an Attention layer `layer_name` is in the keys of this dict, it
        # means this layer will perform attention using the keys and values
        # from the KV cache of `shared_kv_cache_layers[layer_name]`.
        self.shared_kv_cache_layers: dict[str, str] = {}
        self.kv_sharing_fast_prefill_eligible_layers: set[str] = set()

        self.kv_sharing_fast_prefill_logits_indices = None
        if self.cache_config.kv_sharing_fast_prefill:
            self.kv_sharing_fast_prefill_logits_indices = torch.zeros(
                self.max_num_tokens, dtype=torch.int32, device=self.device
            )

        self.uniform_decode_query_len = 1 + self.num_spec_tokens

        # Cudagraph dispatcher for runtime cudagraph dispatching.
        self.cudagraph_dispatcher = CudagraphDispatcher(self.vllm_config)

        self.mm_budget = (
            MultiModalBudget(self.vllm_config, self.mm_registry)
            if self.supports_mm_inputs
            else None
        )

        self.reorder_batch_threshold: int | None = None

        # Attention layers that are only in the KVCacheConfig of the runner
        # (e.g., KV sharing, encoder-only attention), but not in the
        # KVCacheConfig of the scheduler.
        self.runner_only_attn_layers: set[str] = set()

        # Cached outputs.
        self._draft_token_ids: list[list[int]] | torch.Tensor | None = None
        # N-gram GPU path: async D2H buffer/event for per-request valid draft counts.
        self._num_valid_draft_tokens: torch.Tensor | None = None
        self._num_valid_draft_tokens_cpu: torch.Tensor | None = None
        self._num_valid_draft_tokens_event: torch.cuda.Event | None = None
        self._num_valid_draft_tokens_copy_stream: torch.cuda.Stream | None = None
        if (
            self.speculative_config is not None
            and self.speculative_config.use_ngram_gpu()
        ):
            self._num_valid_draft_tokens_cpu = torch.empty(
                self.max_num_reqs, dtype=torch.int32, pin_memory=self.pin_memory
            )
            self._num_valid_draft_tokens_event = torch.cuda.Event()
            self._num_valid_draft_tokens_copy_stream = torch.cuda.Stream()

        self._draft_token_req_ids: list[str] | None = None
        self.transfer_event = torch.Event()
        self.sampled_token_ids_pinned_cpu = torch.empty(
            (self.max_num_reqs, 1),
            dtype=torch.int64,
            device="cpu",
            pin_memory=self.pin_memory,
        )

        # Pre-allocated tensor for copying valid sampled token counts to CPU,
        # with dedicated stream for overlapping and event for coordination.
        self.valid_sampled_token_count_event: torch.Event | None = None
        self.valid_sampled_token_count_copy_stream: torch.cuda.Stream | None = None
        # We also copy the drafted tokens to the CPU asynchronously,
        # in case we need them for structured outputs.
        self.draft_token_ids_event: torch.Event | None = None
        self.draft_token_ids_copy_stream: torch.cuda.Stream | None = None
        self.valid_sampled_token_count_cpu: torch.Tensor | None = None
        self.draft_token_ids_cpu: torch.Tensor | None = None
        self.num_accepted_tokens_event: torch.Event | None = None
        if self.num_spec_tokens:
            self.draft_token_ids_event = torch.Event()
            self.num_accepted_tokens_event = torch.Event()
            self.draft_token_ids_copy_stream = torch.cuda.Stream()
            self.draft_token_ids_cpu = torch.empty(
                (self.max_num_reqs, self.num_spec_tokens),
                dtype=torch.int64,
                device="cpu",
                pin_memory=self.pin_memory,
            )
            if self.use_async_scheduling:
                self.valid_sampled_token_count_event = torch.Event()
                self.valid_sampled_token_count_copy_stream = torch.cuda.Stream()
                self.valid_sampled_token_count_cpu = torch.empty(
                    self.max_num_reqs,
                    dtype=torch.int32,
                    device="cpu",
                    pin_memory=self.pin_memory,
                )

        # Model weight offloader
        # Make sure this is called before any get_offloader call
        set_offloader(create_offloader(self.offload_config))

        # Ephemeral state transferred between execute_model() and sample_tokens().
        self.execute_model_state: ExecuteModelState | None = None
        self.kv_connector_output: KVConnectorOutput | None = None
        self.mamba_state_idx: dict[str, int] = {}
        self._mamba_copy_bufs: mamba_utils.MambaCopyBuffers | None = None
        self.layerwise_nvtx_hooks_registered = False