def __init__(
        self,
        input_dim: int,
        hidden_size: int,
        num_heads: int,
        num_key_value_heads: int,
        head_dim: int,
        use_bias: bool = True,
        use_pytorch_sdpa: bool = False,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()

        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.total_num_heads = num_heads
        tp_size = get_tensor_model_parallel_world_size()

        assert self.hidden_size % self.total_num_heads == 0
        assert self.total_num_heads % tp_size == 0

        self.num_heads = self.total_num_heads // tp_size
        self.head_dim = head_dim

        assert self.head_dim == self.hidden_size // self.total_num_heads

        self.total_num_kv_heads = num_key_value_heads
        if self.total_num_kv_heads >= tp_size:
            assert self.total_num_kv_heads % tp_size == 0
        else:
            assert tp_size % self.total_num_kv_heads == 0

        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)

        self.kv_size = self.num_kv_heads * self.head_dim

        self.q_proj = ColumnParallelLinear(
            self.input_dim,
            self.total_num_heads * self.head_dim,
            bias=use_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.q_proj",
        )
        self.merged_kv = MergedColumnParallelLinear(
            self.input_dim,
            [self.total_num_kv_heads * self.head_dim] * 2,
            bias=use_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.merged_kv",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            self.hidden_size,
            bias=use_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )
        self.scale = self.head_dim**-0.5
        self.use_pytorch_sdpa = use_pytorch_sdpa
        if use_pytorch_sdpa:
            self.attn = None
        else:
            self.attn = MMEncoderAttention(
                self.num_heads,
                self.head_dim,
                self.scale,
                num_kv_heads=self.num_kv_heads,
                prefix=f"{prefix}.attn",
            )