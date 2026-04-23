def __init__(self, *, vllm_config: VllmConfig, prefix: str = "", **kwargs) -> None:
        super().__init__()
        config = vllm_config.model_config.hf_config
        cache_config = vllm_config.cache_config
        quant_config = vllm_config.quant_config
        self.hidden_size = config.hidden_size
        tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = config.num_attention_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
        self.total_num_kv_heads = config.num_key_value_heads
        if self.total_num_kv_heads >= tp_size:
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_kv_heads % tp_size == 0
        else:
            # Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)
        self.head_dim = config.hidden_size_per_head
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.scaling = self.head_dim**-0.5

        self.qkv_proj = QKVParallelLinear(
            config.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            config.hidden_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        max_position = config.max_position_embeddings
        if hasattr(vllm_config.model_config, "max_model_len") and isinstance(
            vllm_config.model_config.max_model_len, int
        ):
            max_position = min(max_position, vllm_config.model_config.max_model_len)

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=max_position,
            rope_parameters=config.rope_parameters,
        )
        self.q_norm = RMSNorm(config.hidden_size_per_head, eps=config.rms_norm_eps)
        self.q_norm.weight = torch.nn.Parameter(
            torch.ones((self.num_heads, config.hidden_size_per_head))
        )
        set_weight_attrs(
            self.q_norm.weight, {"weight_loader": sharded_weight_loader(0)}
        )
        self.k_norm = RMSNorm(config.hidden_size_per_head, eps=config.rms_norm_eps)
        self.k_norm.weight = torch.nn.Parameter(
            torch.ones((self.num_kv_heads, config.hidden_size_per_head))
        )
        # Tensor-parallelism shards the K norm weights to the tp ranks
        # in a head-wise manner. This approach does not work if there is only
        # a single KV head, as is the case for PLaMo 2-1B.
        if self.total_num_kv_heads != 1:
            set_weight_attrs(
                self.k_norm.weight, {"weight_loader": sharded_weight_loader(0)}
            )

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            prefix=f"{prefix}.attn",
        )