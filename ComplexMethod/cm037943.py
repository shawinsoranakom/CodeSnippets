def __init__(self, config: PretrainedConfig, **kwargs: Any) -> None:
        super().__init__()
        self.config = config
        # n_embed or hidden_size for text LM
        hidden_size = config.n_embd if hasattr(config, "n_embd") else config.hidden_size

        # self.wte = nn.Embedding(config.vocab_size, hidden_size)

        audio_dim_out = (
            None  # Set this variable according to the actual audio processor
        )
        self.layer_idx = -2

        if (
            isinstance(config.audio_processor, dict)
            and config.audio_processor.get("name", None) == "cascades"
        ):
            encoder_config = config.audio_processor.get("config", None)
            assert encoder_config is not None
            self.encoder = ConformerEncoder(**encoder_config)

            audio_dim_out = encoder_config["attention_dim"]
            n_mels = encoder_config["input_size"]
        else:
            raise NotImplementedError("")

        assert audio_dim_out is not None, "Remember to set values for audio_dim_out"
        self.audio_dim_out = audio_dim_out
        self.audio_dim_in = n_mels

        self.freeze_audio_processor = kwargs.get("freeze_audio_processor", False)

        self.downsample_rate = kwargs.get("downsample_rate", 1)

        if kwargs.get("use_qformer", False):
            qformer_config = kwargs.get("qformer_config", {})
            qformer_config["attention_dim"] = audio_dim_out
            self.qformer = WindowQformer(**qformer_config)
        else:
            self.qformer = None

        if kwargs.get("use_conv_downsample", False):
            assert self.qformer is None, (
                "don't support use qformer and conv downsample together"
            )
            nemo_conv_settings = kwargs.get("nemo_conv_settings", {})
            default_nemo_conv_settings = {
                "subsampling": "dw_striding",
                "subsampling_factor": self.downsample_rate,
                "feat_in": audio_dim_out,
                "feat_out": audio_dim_out,
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

            self.conv_ds = NemoConvSubsampling(
                **default_nemo_conv_settings,
            )
        else:
            self.conv_ds = None

        projection_cls = kwargs.get("projection_cls", "linear")
        if projection_cls == "linear":
            self.audio_projection = nn.Linear(audio_dim_out, hidden_size)
        elif projection_cls == "mlp":
            # follow llava-v1.5's implementation
            # (do not use image_projection and image_proj_norm)
            dim_projection = hidden_size
            depth = 2
            self.linear_downsample_rate = (
                1 if (self.qformer or self.conv_ds) else self.downsample_rate
            )
            layers = [
                nn.Linear(audio_dim_out * self.linear_downsample_rate, dim_projection)
            ]
            for _ in range(1, depth):
                layers.extend([nn.GELU(), nn.Linear(dim_projection, dim_projection)])
            self.audio_projection = nn.Sequential(*layers)
            # NOTE vision-speech tasks use a separate projection layer
            layers = [
                nn.Linear(audio_dim_out * self.linear_downsample_rate, dim_projection)
            ]
            for _ in range(1, depth):
                layers.extend([nn.GELU(), nn.Linear(dim_projection, dim_projection)])
            self.audio_projection_for_vision = nn.Sequential(*layers)
        else:
            raise NotImplementedError(
                f"projection_cls = {projection_cls}, not implemented"
            )

        # TODO: audio sequence compression - Qformer
        self.vocab_size = config.vocab_size
        self.input_embeds = None
        self.audio_embed_sizes = None