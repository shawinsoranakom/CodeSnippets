def __init__(self, vllm_config: VllmConfig, device: torch.device):
        self.vllm_config = vllm_config
        self.model_config = vllm_config.model_config
        self.cache_config = vllm_config.cache_config
        self.compilation_config = vllm_config.compilation_config
        self.lora_config = vllm_config.lora_config
        self.load_config = vllm_config.load_config
        self.parallel_config = vllm_config.parallel_config
        self.scheduler_config = vllm_config.scheduler_config
        self.speculative_config = vllm_config.speculative_config
        self.observability_config = vllm_config.observability_config

        self.device = device
        self.dtype = self.model_config.dtype
        self.kv_cache_dtype = self.dtype
        if self.cache_config.cache_dtype != "auto":
            # Quantized KV cache.
            self.kv_cache_dtype = STR_DTYPE_TO_TORCH_DTYPE[
                self.cache_config.cache_dtype
            ]

        self.vocab_size = self.model_config.get_vocab_size()
        self.max_model_len = self.model_config.max_model_len
        self.max_num_tokens = self.scheduler_config.max_num_batched_tokens
        self.max_num_reqs = self.scheduler_config.max_num_seqs
        self.is_encoder_decoder = self.model_config.is_encoder_decoder

        self.use_async_scheduling = self.scheduler_config.async_scheduling
        self.output_copy_stream = torch.cuda.Stream(self.device)

        # Pipeline parallelism.
        self.use_pp = self.parallel_config.pipeline_parallel_size > 1
        self.is_first_pp_rank = get_pp_group().is_first_rank
        self.is_last_pp_rank = get_pp_group().is_last_rank

        # Persistent buffer for intermediate tensors (non-first PP ranks).
        self.intermediate_tensors: IntermediateTensors | None = None

        # Data parallelism.
        self.dp_size = self.parallel_config.data_parallel_size
        self.dp_rank = self.parallel_config.data_parallel_rank

        # Decode context parallelism.
        self.dcp_size = self.parallel_config.decode_context_parallel_size
        self.use_dcp = self.dcp_size > 1
        self.dcp_rank = get_dcp_group().rank_in_group if self.use_dcp else 0
        self.cp_interleave = self.parallel_config.cp_kv_cache_interleave_size

        # Multimodal
        self.mm_registry = MULTIMODAL_REGISTRY
        self.supports_mm_inputs = self.mm_registry.supports_multimodal_inputs(
            self.model_config
        )
        self.encoder_cache = None
        if self.supports_mm_inputs and self.is_first_pp_rank:
            self.encoder_cache = EncoderCache()

        # Speculative decoding.
        self.speculator = None
        self.num_speculative_steps = 0
        self.use_aux_hidden_state_outputs = False
        if self.speculative_config is not None:
            self.num_speculative_steps = self.speculative_config.num_speculative_tokens

            if self.is_last_pp_rank:
                self.speculator = init_speculator(self.vllm_config, self.device)

            if self.speculative_config.method == "eagle3":
                # EAGLE3 may require auxiliary hidden states from target model outputs.
                self.use_aux_hidden_state_outputs = True
                if self.use_pp:
                    raise ValueError("EAGLE3 with pipeline parallel is not supported.")

        # Draft tokens propagation - for spec-dec + struct outputs.
        self.draft_tokens_handler = DraftTokensHandler(self.device)
        self.uniform_decode_query_len = 1 + self.num_speculative_steps

        # Pooling models.
        self.is_pooling_model = self.model_config.runner_type == "pooling"
        self.pooling_runner: PoolingRunner | None = None

        # General request states.
        self.req_states = RequestState(
            max_num_reqs=self.max_num_reqs,
            max_model_len=self.max_model_len,
            max_num_batched_tokens=self.max_num_tokens,
            num_speculative_steps=self.num_speculative_steps,
            vocab_size=self.vocab_size,
            device=self.device,
        )
        self.input_buffers = InputBuffers(
            max_num_reqs=self.max_num_reqs,
            max_num_tokens=self.max_num_tokens,
            device=self.device,
        )

        self.sampler: Sampler | None = None
        self.rejection_sampler: RejectionSampler | None = None
        self.prompt_logprobs_worker: PromptLogprobsWorker | None = None
        self.structured_outputs_worker: StructuredOutputsWorker | None = None
        if self.is_last_pp_rank and not self.is_pooling_model:
            # Initialize sampling-related workers.
            # These components are only set up on the last PP rank and
            # for generative (non-pooling) models.
            self.sampler = Sampler(
                max_num_reqs=self.max_num_reqs,
                vocab_size=self.vocab_size,
                device=self.device,
                req_states=self.req_states,
                logprobs_mode=self.model_config.logprobs_mode,
                num_speculative_tokens=self.num_speculative_steps + 1,
            )
            if self.speculative_config is not None:
                self.rejection_sampler = RejectionSampler(
                    self.sampler,
                    self.speculative_config,
                )
            self.prompt_logprobs_worker = PromptLogprobsWorker(self.max_num_reqs)
            self.structured_outputs_worker = StructuredOutputsWorker(
                max_num_logits=self.max_num_reqs * (self.num_speculative_steps + 1),
                vocab_size=self.vocab_size,
                device=self.device,
            )

        # For CUDA graphs, and will init cudagraph_manager after init_attn_backend.
        self.decode_query_len = self.num_speculative_steps + 1
        self.cudagraph_manager: ModelCudaGraphManager | None = None
        # LoRA-related workers.
        self.lora_state = LoraState(max_num_reqs=self.max_num_reqs)
        # KV Connector if configured.
        self.kv_connector: KVConnector = NO_OP_KV_CONNECTOR

        # For transferring state from execute_model to subsequent sample_tokens call.
        self.execute_model_state: ExecuteModelState | None = None

        # Expert parallelism load balancer.
        self.eplb = EPLBController(self.parallel_config, self.device)