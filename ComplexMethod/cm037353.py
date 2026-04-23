def __init__(
        self,
        vllm_config: VllmConfig,
        device: torch.device,
        dtype: torch.dtype,
        model: SupportsEncoderCudaGraph,
    ):
        """Initialize CUDA graph manager with provided token budgets
        and max batch size."""
        self.vllm_config = vllm_config
        self.device = device
        self.dtype = dtype
        self.model = model
        self.config: EncoderCudaGraphConfig = model.get_encoder_cudagraph_config()

        comp_config = vllm_config.compilation_config
        user_budgets = comp_config.encoder_cudagraph_token_budgets
        user_max_vision_items = comp_config.encoder_cudagraph_max_vision_items_per_batch
        user_max_frames = comp_config.encoder_cudagraph_max_frames_per_batch

        multimodal_config = vllm_config.model_config.multimodal_config

        if user_budgets and user_max_vision_items > 0:
            # Fully user-specified
            self.token_budgets = sorted(user_budgets)
            self.max_batch_size = user_max_vision_items
        else:
            # Auto-infer missing values from model
            min_budget, max_budget = model.get_encoder_cudagraph_budget_range(
                vllm_config
            )
            self.token_budgets = (
                sorted(user_budgets)
                if user_budgets
                else self._generate_budgets(min_budget, max_budget)
            )
            self.max_batch_size = (
                user_max_vision_items
                if user_max_vision_items > 0
                else max_budget // min_budget
            )

        assert multimodal_config is not None
        if multimodal_config.get_limit_per_prompt("video") == 0:
            self.max_frames_per_batch = 0
        elif user_max_frames is not None:
            self.max_frames_per_batch = user_max_frames
        else:
            # Set it to the model-specific value according to its `processing_info`.
            max_frames_per_video = self.model.get_max_frames_per_video()
            self.max_frames_per_batch = self.max_batch_size * max_frames_per_video

        mm_config = vllm_config.model_config.multimodal_config
        self.use_dp = (
            mm_config is not None
            and mm_config.mm_encoder_tp_mode == "data"
            and vllm_config.parallel_config.tensor_parallel_size > 1
        )

        self.budget_graphs: dict[int, BudgetGraphMetadata] = {}
        self.graph_hits = 0
        self.graph_misses = 0
        self.log_stats_interval = 100

        logger.info(
            "EncoderCudaGraphManager initialized with "
            "budgets=%s, max_batch_size=%d, max_frames_per_batch=%s, use_dp=%s",
            self.token_budgets,
            self.max_batch_size,
            self.max_frames_per_batch,
            self.use_dp,
        )