def __post_init__(self, **kwargs):
        if kwargs.pop("tie_word_embeddings", False):
            raise ValueError("`tie_word_embeddings=True` is not supported for CsmConfig")

        if self.depth_decoder_config is None:
            self.depth_decoder_config = CsmDepthDecoderConfig()
            logger.info("depth_decoder_config is None, using default depth decoder config.")
        elif isinstance(self.depth_decoder_config, dict):
            self.depth_decoder_config = CsmDepthDecoderConfig(**self.depth_decoder_config)

        if self.codec_config is None:
            self.codec_config = AutoConfig.for_model("mimi")
            logger.info("codec_config is None, using default audio encoder config.")
        elif isinstance(self.codec_config, dict):
            self.codec_config = AutoConfig.for_model(**self.codec_config)

        if self.num_key_value_heads is None:
            self.num_key_value_heads = self.num_attention_heads

        self.head_dim = self.head_dim if self.head_dim is not None else self.hidden_size // self.num_attention_heads
        self.tie_word_embeddings = False
        super().__post_init__(**kwargs)