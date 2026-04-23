def __init__(
        self,
        config: PretrainedConfig,
        hidden_size: int,
        num_heads: int,
        num_kv_heads: int,
        rope_parameters: dict[str, Any] | None = None,
        max_position_embeddings: int = 8192,
        quant_config: QuantizationConfig | None = None,
        bias: bool = False,
        bias_o_proj: bool = False,
        cache_config: CacheConfig | None = None,
        prefix: str = "",
        attn_type: str = AttentionType.DECODER,
    ) -> None:
        super().__init__()
        layer_idx = extract_layer_index(prefix)
        self.hidden_size = hidden_size
        self.tp_size = get_tensor_model_parallel_world_size()
        self.tp_rank = get_tensor_model_parallel_rank()
        self.total_num_heads = num_heads
        if self.total_num_heads % self.tp_size != 0:
            raise ValueError(
                f"total_num_heads {self.total_num_heads} "
                f"is not divisible by tp_size {self.tp_size}."
            )
        self.num_heads = self.total_num_heads // self.tp_size
        self.total_num_kv_heads = num_kv_heads
        if (
            self.total_num_kv_heads > self.tp_size
            and self.total_num_kv_heads % self.tp_size != 0
        ):
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel ranks.
            raise ValueError(
                "Number of KV heads is greater than TP size, "
                f"but total_num_kv_heads {self.total_num_kv_heads} "
                f"is not divisible by tp_size {self.tp_size}."
            )
        elif self.total_num_kv_heads < self.tp_size:
            # TODO: Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel ranks.
            raise ValueError(
                f"Number of KV heads {self.total_num_kv_heads} is less than "
                f"TP size {self.tp_size}, KV heads replication is not support yet."
            )
        self.num_kv_heads = max(1, self.total_num_kv_heads // self.tp_size)
        self.qk_nope_dim = getattr(config, "qk_nope_dim", None)
        self.qk_rope_dim = getattr(config, "qk_rope_dim", None)
        self.v_channels = getattr(config, "v_channels", None)
        self.head_dim = self.qk_rope_dim + self.qk_nope_dim
        self.q_size = self.num_heads * self.head_dim
        self.k_size = self.num_kv_heads * self.head_dim
        self.v_size = self.num_kv_heads * self.v_channels
        self.scaling = self.head_dim**-0.5
        self.max_position_embeddings = max_position_embeddings

        self.param_sink_number = getattr(config, "param_sink_number", 0)
        self.param_sink_with_value = getattr(config, "param_sink_with_value", False)
        self.param_sink_scalar = getattr(config, "param_sink_scalar", None)
        self.param_sink_of_head_num = getattr(config, "param_sink_of_head_dim", False)

        self.qkv_proj = MergedColumnParallelLinear(
            input_size=hidden_size,
            output_sizes=[
                self.q_size * self.tp_size,
                self.k_size * self.tp_size,
                self.v_size * self.tp_size,
            ],
            bias=bias,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )

        self.o_proj = RowParallelLinear(
            input_size=self.total_num_heads * self.v_channels,
            output_size=hidden_size,
            bias=bias_o_proj,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        self.k_layernorm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)

        self._init_rotary_emb(
            config, rope_parameters=rope_parameters, quant_config=quant_config
        )

        if hasattr(config, "interleaved_sliding_window"):
            interleaved_sliding_window = config.interleaved_sliding_window
            if isinstance(interleaved_sliding_window, int):
                sliding_window = interleaved_sliding_window
            elif isinstance(interleaved_sliding_window, list):
                sw_idx = layer_idx % len(interleaved_sliding_window)
                sliding_window = interleaved_sliding_window[sw_idx]
            else:
                raise ValueError(
                    f"{type(interleaved_sliding_window)} "
                    "for interleaved_sliding_window is not supported."
                )
        else:
            sliding_window = None

        FlashAttentionDiffKVBackend.set_head_size_v(self.v_channels)
        self.attn = StaticSinkAttention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            sink_len=self.param_sink_number,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            per_layer_sliding_window=sliding_window,
            attn_type=attn_type,
            prefix=f"{prefix}.attn",
            attn_backend=FlashAttentionDiffKVBackend,
            head_size_v=self.v_channels,
        )

        if self.param_sink_number > 0:
            self.param_sink_key = torch.nn.Parameter(
                torch.empty(
                    (
                        self.param_sink_number,
                        self.num_kv_heads,
                        self.head_dim,
                    ),
                    device=current_platform.current_device(),
                    dtype=config.torch_dtype,
                )
            )
            set_weight_attrs(
                self.param_sink_key,
                {
                    "output_dim": 1,
                    "weight_loader": self.weight_loader,
                },
            )

            if self.param_sink_with_value:
                self.param_sink_value = torch.nn.Parameter(
                    torch.empty(
                        (
                            self.param_sink_number,
                            self.num_kv_heads,
                            self.v_channels,
                        ),
                        device=current_platform.current_device(),
                        dtype=config.torch_dtype,
                    )
                )
                set_weight_attrs(
                    self.param_sink_value,
                    {
                        "output_dim": 1,
                        "weight_loader": self.weight_loader,
                    },
                )
            else:
                self.param_sink_value = torch.zeros(
                    (
                        self.param_sink_number,
                        self.num_kv_heads,
                        self.v_channels,
                    ),
                    device=current_platform.current_device(),
                    dtype=config.torch_dtype,
                )
        # To enable dummy run with out weight
        self.post_weight_load()