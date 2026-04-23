def __init__(self, *, vllm_config: VllmConfig, prefix: str = ""):
        super().__init__()
        config = vllm_config.model_config.hf_config
        quant_config = vllm_config.quant_config

        self.config = config

        self.quant_config = quant_config

        self.model = MixtralModel(
            vllm_config=vllm_config, prefix=maybe_prefix(prefix, "model")
        )

        self.lm_head = ParallelLMHead(
            config.vocab_size,
            config.hidden_size,
            quant_config=quant_config,
            prefix=maybe_prefix(prefix, "lm_head"),
        )
        if self.config.tie_word_embeddings:
            self.lm_head.weight = self.model.embed_tokens.weight
        self.logits_processor = LogitsProcessor(config.vocab_size)
        self.make_empty_intermediate_tensors = (
            self.model.make_empty_intermediate_tensors
        )

        self.expert_weights = []
        self.moe_layers = []
        example_moe = None

        for layer in self.model.layers:
            if isinstance(layer, PPMissingLayer):
                continue
            assert isinstance(layer, MixtralDecoderLayer)
            if hasattr(layer, "block_sparse_moe") and isinstance(
                layer.block_sparse_moe, MixtralMoE
            ):
                example_moe = layer.block_sparse_moe
                self.moe_layers.append(layer.block_sparse_moe.experts)

        self.num_moe_layers = len(self.moe_layers)

        if example_moe is None:
            raise RuntimeError("No MixtralMoE layer found  in model.layers.")

        self.num_logical_experts = example_moe.n_logical_experts
        self.num_physical_experts = example_moe.n_physical_experts
        self.num_local_physical_experts = example_moe.n_local_physical_experts
        self.num_routed_experts = example_moe.n_routed_experts
        self.num_redundant_experts = example_moe.n_redundant_experts
        self.num_expert_groups = 1
        self.num_shared_experts = 0