def __init__(
        self,
        input_size: int,
        chunk_size: int | list[int],
        left_chunk: int | list[int],
        attention_dim: int = 256,
        attention_heads: int = 4,
        input_layer: str = "nemo_conv",
        cnn_out: int = -1,
        cnn_layer_norm: bool = False,
        time_reduction: int = 4,
        dropout_rate: float = 0.0,
        padding_idx: int = -1,
        relative_attention_bias_args: dict[str, Any] | None = None,
        positional_dropout_rate: float = 0.0,
        nemo_conv_settings: dict[str, Any] | None = None,
        conv2d_extra_padding: Literal["feat", "feat_time", "none", True] = "none",
        attention_group_size: int = 1,
        encoder_embedding_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.input_size = input_size
        self.input_layer = input_layer
        self.chunk_size = chunk_size
        self.left_chunk = left_chunk
        self.attention_dim = attention_dim
        self.num_heads = attention_heads
        self.attention_group_size = attention_group_size
        self.time_reduction = time_reduction
        self.nemo_conv_settings = nemo_conv_settings
        self.encoder_embedding_config = encoder_embedding_config

        if self.input_layer == "nemo_conv":
            default_nemo_conv_settings = {
                "subsampling": "dw_striding",
                "subsampling_factor": self.time_reduction,
                "feat_in": input_size,
                "feat_out": attention_dim,
                "conv_channels": 256,
                "subsampling_conv_chunking_factor": 1,
                "activation": nn.ReLU(),
                "is_causal": False,
            }
            # Override any of the defaults with the incoming, user settings
            if nemo_conv_settings:
                default_nemo_conv_settings.update(nemo_conv_settings)
                for i in ["subsampling_factor", "feat_in", "feat_out"]:
                    assert i not in nemo_conv_settings, (
                        "{i} should be specified outside of the NeMo dictionary"
                    )

            self.embed = NemoConvSubsampling(
                **default_nemo_conv_settings,
            )
        else:
            raise ValueError("unknown input_layer: " + input_layer)

        self.pos_emb = AbsolutePositionalEncoding(
            attention_dim, positional_dropout_rate
        )

        self.relative_attention_bias_type = (
            relative_attention_bias_args.get("type")
            if relative_attention_bias_args
            else None
        )
        if self.relative_attention_bias_type == "t5":
            assert self.num_heads % self.attention_group_size == 0, (
                "attention_group_size must divide n_head"
            )
            self.relative_attention_bias_layer = T5RelativeAttentionLogitBias(
                self.num_heads // self.attention_group_size,
                max_distance=relative_attention_bias_args.get(
                    "t5_bias_max_distance", 1000
                ),
                symmetric=relative_attention_bias_args.get("t5_bias_symmetric", False),
            )
        else:
            raise NotImplementedError

        self.encoder_embedding = MeanVarianceNormLayer(
            self.encoder_embedding_config["input_size"]
        )