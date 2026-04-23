def __init__(self, *, vllm_config: VllmConfig, prefix: str = "") -> None:
        config = vllm_config.model_config.hf_config
        quant_config = vllm_config.quant_config
        cache_config = vllm_config.cache_config

        if cache_config.mamba_cache_mode == "all":
            raise NotImplementedError(
                "Lfm2Moe currently does not support 'all' prefix caching, "
                "please use '--mamba-cache-mode=align' instead"
            )

        super().__init__()
        self.config = config
        self.model = Lfm2MoeModel(
            vllm_config=vllm_config, prefix=maybe_prefix(prefix, "model")
        )

        if get_pp_group().is_last_rank:
            self.lm_head = ParallelLMHead(
                config.vocab_size,
                config.hidden_size,
                quant_config=quant_config,
                prefix=maybe_prefix(prefix, "lm_head"),
            )
            self.lm_head = self.lm_head.tie_weights(self.model.embed_tokens)
        else:
            self.lm_head = PPMissingLayer()

        self.logits_processor = LogitsProcessor(config.vocab_size)

        self.make_empty_intermediate_tensors = (
            self.model.make_empty_intermediate_tensors
        )

        # Set MoE hyperparameters
        self.expert_weights = []

        self.moe_layers = []
        example_layer = None
        for layer in self.model.layers:
            if isinstance(layer, PPMissingLayer):
                continue

            assert isinstance(
                layer, (Lfm2MoeAttentionDecoderLayer, Lfm2MoeShortConvDecoderLayer)
            )
            if isinstance(layer.feed_forward, Lfm2MoeSparseMoeBlock):
                example_layer = layer.feed_forward
                self.moe_layers.append(layer.feed_forward.experts)

        if example_layer is None:
            raise RuntimeError(
                "No Lfm2MoeSparseMoeBlock layer found in the model.layers."
            )

        self.num_moe_layers = len(self.moe_layers)
        self.num_expert_groups = 1
        self.num_shared_experts = 0
        self.num_logical_experts = example_layer.n_logical_experts
        self.num_physical_experts = example_layer.n_physical_experts
        self.num_local_physical_experts = example_layer.n_local_physical_experts
        self.num_routed_experts = example_layer.n_routed_experts
        self.num_redundant_experts = example_layer.n_redundant_experts