def __init__(
        self,
        config: FalconConfig,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ):
        super().__init__()

        self.hidden_size = config.hidden_size
        tp_size = get_tensor_model_parallel_world_size()

        self.total_num_heads = config.num_attention_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
        self.head_dim = self.hidden_size // self.total_num_heads
        assert self.head_dim * self.total_num_heads == self.hidden_size

        self.new_decoder_architecture = config.new_decoder_architecture
        self.multi_query = config.multi_query

        if self.new_decoder_architecture:
            self.total_num_kv_heads = config.num_kv_heads
        elif self.multi_query:
            self.total_num_kv_heads = 1
        else:
            self.total_num_kv_heads = self.total_num_heads
        if self.total_num_kv_heads >= tp_size:
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_kv_heads % tp_size == 0
        else:
            # Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)

        self.query_key_value = QKVParallelLinear(
            self.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=config.bias,
            skip_bias_add=True,
            quant_config=quant_config,
            prefix=f"{prefix}.query_key_value",
        )
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim

        # Layer-wise attention scaling
        self.inv_norm_factor = 1.0 / math.sqrt(self.head_dim)
        self.reduce_row_parallel_results = not (
            config.new_decoder_architecture or config.parallel_attn
        )
        self.dense = RowParallelLinear(
            self.hidden_size,
            self.hidden_size,
            bias=config.bias,
            skip_bias_add=True,
            quant_config=quant_config,
            reduce_results=self.reduce_row_parallel_results,
            prefix=f"{prefix}.dense",
        )

        self.use_rotary = config.rotary
        self.use_alibi = config.alibi
        assert not (self.use_rotary and self.use_alibi), (
            "Rotary and alibi are mutually exclusive."
        )

        if self.use_rotary:
            max_position_embeddings = getattr(config, "max_position_embeddings", 8192)
            self.rotary_emb = get_rope(
                self.head_dim,
                max_position=max_position_embeddings,
                rope_parameters=config.rope_parameters,
            )
            self.attn = Attention(
                self.num_heads,
                self.head_dim,
                self.inv_norm_factor,
                num_kv_heads=self.num_kv_heads,
                quant_config=quant_config,
                prefix=f"{prefix}.attn",
            )
        elif self.use_alibi:
            tp_rank = get_tensor_model_parallel_rank()
            head_start = tp_rank * self.num_heads
            head_end = (tp_rank + 1) * self.num_heads
            alibi_slopes = (
                _get_alibi_slopes(self.total_num_heads) * self.inv_norm_factor
            )
            alibi_slopes = alibi_slopes[head_start:head_end].tolist()
            self.attn = Attention(
                self.num_heads,
                self.head_dim,
                self.inv_norm_factor,
                num_kv_heads=self.num_kv_heads,
                alibi_slopes=alibi_slopes,
                quant_config=quant_config,
                prefix=f"{prefix}.attn",
            )
        else:
            self.attn = Attention(
                self.num_heads,
                self.head_dim,
                scale=self.inv_norm_factor,
                num_kv_heads=self.num_kv_heads,
                cache_config=cache_config,
                quant_config=quant_config,
                prefix=f"{prefix}.attn",
            )