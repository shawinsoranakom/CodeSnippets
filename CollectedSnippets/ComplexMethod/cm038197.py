def __init__(
        self,
        config: MptConfig,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ):
        super().__init__()
        self.d_model = config.d_model
        self.total_num_heads = config.n_heads
        self.head_dim = self.d_model // self.total_num_heads
        self.clip_qkv = config.attn_config.clip_qkv
        self.qk_ln = config.attn_config.qk_ln
        self.alibi_bias_max = config.attn_config.alibi_bias_max
        if "kv_n_heads" in config.attn_config:
            self.total_num_kv_heads = config.attn_config.kv_n_heads
        else:
            self.total_num_kv_heads = self.total_num_heads
        assert not config.attn_config.prefix_lm
        assert config.attn_config.alibi

        # pylint: disable=invalid-name
        self.Wqkv = QKVParallelLinear(
            self.d_model,
            self.d_model // self.total_num_heads,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=not config.no_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.Wqkv",
        )
        if self.qk_ln:
            self.q_ln = nn.LayerNorm(self.d_model)
            self.k_ln = nn.LayerNorm(self.d_model)
        self.out_proj = RowParallelLinear(
            self.d_model,
            self.d_model,
            bias=not config.no_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.out_proj",
        )

        tp_world_size = get_tensor_model_parallel_world_size()
        assert self.total_num_heads % tp_world_size == 0
        self.num_heads = self.total_num_heads // tp_world_size

        if self.total_num_kv_heads >= tp_world_size:
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_kv_heads % tp_world_size == 0
        else:
            # Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_world_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_world_size)
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        # Create the alibi slopes and slice them.
        tp_rank = get_tensor_model_parallel_rank()
        head_start = tp_rank * self.num_heads
        head_end = (tp_rank + 1) * self.num_heads
        alibi_slopes = _get_alibi_slopes(self.total_num_heads, self.alibi_bias_max)
        alibi_slopes = alibi_slopes[head_start:head_end].tolist()

        self.head_dim = self.d_model // self.total_num_heads
        scaling = self.head_dim**-0.5
        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            scaling,
            alibi_slopes=alibi_slopes,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            prefix=f"{prefix}.attn",
        )