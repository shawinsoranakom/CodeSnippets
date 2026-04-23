def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        bias: bool = True,
        attn_type: AttentionType = AttentionType.DECODER,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ):
        super().__init__()
        self.embed_dim = embed_dim
        tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = num_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
        if self.total_num_heads >= tp_size:
            # Number of heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_heads % tp_size == 0
        else:
            # Number of heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_size % self.total_num_heads == 0
        self.num_kv_heads = max(1, self.total_num_heads // tp_size)
        self.head_dim = self.embed_dim // self.total_num_heads
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.attn_type = attn_type

        if (self.head_dim * num_heads) != self.embed_dim:
            raise ValueError(
                f"embed_dim must be divisible by num_heads (got `embed_dim`: "
                f"{self.embed_dim} and `num_heads`: {num_heads})."
            )
        self.scaling = self.head_dim**-0.5

        self._init_qkv(embed_dim, bias, quant_config, prefix=prefix)

        self.out_projection = RowParallelLinear(
            input_size=embed_dim,
            output_size=embed_dim,
            bias=bias,
            quant_config=quant_config,
            prefix=f"{prefix}.out_projection",
        )
        if attn_type == AttentionType.ENCODER:
            raise NotImplementedError(
                "CohereASRAttention does not support Encoder Self-Attention yet."
            )

        elif self.attn_type == AttentionType.ENCODER_DECODER:
            self.attn = CrossAttention(
                self.num_heads,
                self.head_dim,
                self.scaling,
                num_kv_heads=self.num_kv_heads,
                cache_config=cache_config,
                quant_config=quant_config,
                prefix=f"{prefix}.attn",
                attn_type=self.attn_type,
            )
        else:  # AttentionType.DECODER (regular decoder self-attention)
            self.attn = Attention(
                self.num_heads,
                self.head_dim,
                self.scaling,
                num_kv_heads=self.num_kv_heads,
                cache_config=cache_config,
                quant_config=quant_config,
                prefix=f"{prefix}.attn",
                attn_type=self.attn_type,
            )