def __init__(
        self,
        config: Zamba2Config,
        bare_block_idx: int,
        num_hybrid_layers: int,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ) -> None:
        """Initialize the attention layer.

        Args:
            config: The Zamba2 model configuration
            bare_block_idx: Index of the bare attention block
            num_hybrid_layers: Total number of hybrid layers
            cache_config: Configuration for key-value caching
            quant_config: Configuration for model quantization
            prefix: Optional prefix for parameter names
        """
        super().__init__()
        tp_size = get_tensor_model_parallel_world_size()
        self.config = config
        self.num_hybrid_layers = num_hybrid_layers

        self.attention_hidden_size = config.attention_hidden_size
        self.total_num_attention_heads = config.num_attention_heads
        assert self.total_num_attention_heads % tp_size == 0
        self.num_attention_heads = config.num_attention_heads // tp_size
        self.attention_head_dim = config.attention_head_dim
        self.qkv_size = self.attention_hidden_size // tp_size
        self.scale = (self.attention_head_dim / 2) ** -0.5

        if (
            self.attention_head_dim * self.total_num_attention_heads
        ) != self.attention_hidden_size:
            raise ValueError(
                f"attention_hidden_size must be divisible by"
                f" num_attention_heads"
                f" (got `attention_hidden_size`: {self.attention_hidden_size}"
                f" and `num_heads`: {self.num_attention_heads})."
            )

        self.qkv_proj = QKVParallelLinear(
            self.attention_hidden_size,
            self.attention_head_dim,
            self.total_num_attention_heads,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.attention_hidden_size,
            config.hidden_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        # Even though in Zamba2 weights are shared between attention layers, KV
        # cache is unique for every attention layer. Hence, we need to define
        # separate Attention objects, because in recent vLLM KV cache tensors
        # are tied to specific Attention objects.

        # Initialize attention blocks with proper indexing
        self.dpa_list = nn.ModuleList([])
        j = (
            bare_block_idx
            * (self.num_hybrid_layers + config.num_mem_blocks - 1)
            // config.num_mem_blocks
        )
        for block_idx in range(self.num_hybrid_layers):
            if block_idx % config.num_mem_blocks == bare_block_idx:
                dpa = Attention(
                    self.num_attention_heads,
                    self.attention_head_dim,
                    self.scale,
                    cache_config=cache_config,
                    prefix=f"{prefix}.attn.{j}",
                )
                j += 1
            else:
                dpa = nn.Identity()
            self.dpa_list.append(dpa)

        # Initialize adapter layers if enabled
        if config.use_shared_attention_adapter:
            self.linear_q_adapter_list = nn.ModuleList([])
            self.linear_k_adapter_list = nn.ModuleList([])
            self.linear_v_adapter_list = nn.ModuleList([])

            for block_idx in range(self.num_hybrid_layers):
                if block_idx % config.num_mem_blocks == bare_block_idx:
                    linear_q_adapter = Zamba2LoRA(
                        self.attention_hidden_size,
                        config.adapter_rank,
                        self.attention_hidden_size,
                        quant_config=quant_config,
                        prefix=f"{prefix}.linear_q_adapter",
                    )
                    linear_k_adapter = Zamba2LoRA(
                        self.attention_hidden_size,
                        config.adapter_rank,
                        self.attention_hidden_size,
                        quant_config=quant_config,
                        prefix=f"{prefix}.linear_k_adapter",
                    )
                    linear_v_adapter = Zamba2LoRA(
                        self.attention_hidden_size,
                        config.adapter_rank,
                        self.attention_hidden_size,
                        quant_config=quant_config,
                        prefix=f"{prefix}.linear_v_adapter",
                    )
                else:
                    linear_q_adapter = nn.Identity()
                    linear_k_adapter = nn.Identity()
                    linear_v_adapter = nn.Identity()

                self.linear_q_adapter_list.append(linear_q_adapter)
                self.linear_k_adapter_list.append(linear_k_adapter)
                self.linear_v_adapter_list.append(linear_v_adapter)

        if config.use_mem_rope:
            self.rotary_emb = get_rope(
                head_size=self.attention_head_dim,
                max_position=config.max_position_embeddings,
                rope_parameters=config.rope_parameters,
                is_neox_style=True,
            )