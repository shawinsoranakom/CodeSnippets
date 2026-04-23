def __init__(
        self,
        cache: PagedAttentionCache,
        config: PretrainedConfig,
        generation_config: GenerationConfig,
        continuous_batching_config: ContinuousBatchingConfig,
        logit_processor: ContinuousBatchingLogitsProcessorList,
        input_queue: queue.Queue,
        output_router: OutputRouter,
        stop_event: threading.Event,
        model_device: torch.device,
        model_dtype: torch.dtype,
        scheduler: Scheduler,
    ) -> None:
        """Initialize the continuous batch processor.

        Args:
            cache: A [`PagedAttentionCache`] object
            config: The model configuration
            generation_config: The generation configuration
            continuous_batching_config: The continuous batching configuration
            logit_processor: The [`ContinuousBatchingLogitsProcessorList`] object used to process the logits.
            input_queue: Queue for incoming requests
            output_router: An [`OutputRouter`] object that routes outputs to handlers or the output queue.
            stop_event: Event to signal processing should stop
            model_device: Device for model inputs/outputs
            model_dtype: Data type for model inputs/outputs
            scheduler: The [`Scheduler`] to use
        """
        self.cache = cache
        self.config = config
        self.cb_config = continuous_batching_config
        self.logit_processor = logit_processor
        self.input_queue = input_queue
        self.output_router = output_router
        self.stop_event = stop_event
        self.model_device = model_device
        self.model_dtype = model_dtype
        self.scheduler = scheduler

        # Generation-related attributes
        self.do_sample = getattr(generation_config, "do_sample", True)
        self.return_logprobs = continuous_batching_config.return_logprobs

        # Retrieve the size of the sliding window if there is one
        self.sliding_window = 1 if getattr(config, "sliding_window", None) is None else config.sliding_window
        # Cuda graphs for the generation step
        self.q_padding_interval_size = self.cb_config.q_padding_interval_size
        self.kv_padding_interval_size = self.cb_config.kv_padding_interval_size
        self.max_cached_graphs = self.cb_config.max_cached_graphs
        self.use_cuda_graph_varlen, self.use_cuda_graph_decode = self.cb_config.get_cuda_graph_booleans()

        # Set up metrics collector
        self.max_batch_tokens = cache.max_batch_tokens
        self.metrics = ContinuousBatchProcessorMetrics(cache.max_batch_tokens)

        # If the user turned on the decode fast path (ie. using a block table), check if it is available
        self._ensure_decode_fast_path_is_available()  # this needs to happen before self.inputs_and_outputs is created

        # Resolve compile behavior
        self.cb_config.resolve_compile_configs(
            fallback_compile_config=getattr(generation_config, "compile_config", None),
            is_flash_attn=is_flash_attention_requested(config=config),
            decode_fast_path_available=self.cache.max_blocks_per_request > 0,
        )
        varlen_config, decode_config = self.cb_config.varlen_compile_config, self.cb_config.decode_compile_config

        # Compile the varlen path if config provided
        self._compiled_varlen = None
        if varlen_config is not None:
            self._compiled_varlen = torch.compile(self._forward_process_and_sample, **varlen_config.to_dict())

        # Compile the decode path if config provided
        self._compiled_decode = None
        if decode_config is not None:
            self._compiled_decode = torch.compile(self._forward_process_and_sample, **decode_config.to_dict())

        # Padding is turned on when either cuda graphs or compile is used
        use_cuda_graphs = self.use_cuda_graph_varlen or self.use_cuda_graph_decode
        self._pad_inputs = use_cuda_graphs or (varlen_config is not None or decode_config is not None)

        # Setup inputs and outputs
        self.use_async_batching = self.cb_config.use_async_batching
        if self.use_async_batching:
            # Since in async there are 2 IO pairs, there are also 2 graph buffers: we divide the max_cached_graphs by 2
            max_cached_graphs = ceil(self.max_cached_graphs / 2)
            self.inputs_and_outputs = ContinuousBatchingAsyncIOs(
                cache=cache,
                config=config,
                device=model_device,
                model_dtype=model_dtype,
                max_graphs=max_cached_graphs,
                return_logprobs=self.return_logprobs,
                logit_processor=self.logit_processor,
                use_cuda_graph_varlen=self.use_cuda_graph_varlen,
            )
        else:
            self.inputs_and_outputs = ContinuousBatchingIOs(
                cache=cache,
                config=config,
                device=model_device,
                model_dtype=model_dtype,
                max_graphs=self.max_cached_graphs,
                return_logprobs=self.return_logprobs,
                logit_processor=self.logit_processor,
                use_cuda_graph_varlen=self.use_cuda_graph_varlen,
            )
        # Set up the graph pool. This allows all graphs to share the same memory pool, which is fine because they never
        # run concurrently. This greatly saves memory.
        self.graph_pool = torch.cuda.graph_pool_handle() if use_cuda_graphs else None