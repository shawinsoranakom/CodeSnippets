def __post_init__(self, **kwargs):
        self.num_key_value_heads = (
            self.num_key_value_heads if self.num_key_value_heads is not None else self.num_attention_heads
        )
        self.head_dim = self.head_dim or self.hidden_size // self.num_attention_heads

        if isinstance(self.audio_encoder_config, dict):
            audio_encoder_model_type = self.audio_encoder_config.pop("model_type", "mimi")
            self.audio_encoder_config = AutoConfig.for_model(audio_encoder_model_type, **self.audio_encoder_config)
        elif self.audio_encoder_config is None:
            self.audio_encoder_config = AutoConfig.for_model("mimi")

        self.audio_vocab_size = (
            self.audio_encoder_config.codebook_size if self.audio_vocab_size is None else self.audio_vocab_size
        )

        if isinstance(self.depth_decoder_config, dict):
            self.depth_decoder_config.update(
                {
                    "audio_vocab_size": self.audio_vocab_size,
                    "input_size": self.hidden_size,
                    "vocab_size": self.vocab_size,
                    "num_codebooks": self.num_codebooks,
                }
            )
            self.depth_decoder_config = MoshiDepthConfig(**self.depth_decoder_config)
        elif self.depth_decoder_config is None:
            self.depth_decoder_config = MoshiDepthConfig()
        super().__post_init__(**kwargs)