def __post_init__(self, **kwargs):
        self.encoder_hash_byte_group_size = self.encoder_hash_byte_group_size or [3, 4, 5, 6, 7, 8]

        # Initialize component configurations
        if self.patcher_config is None:
            self.patcher_config = BltPatcherConfig(initializer_range=self.initializer_range)
            logger.info("patcher_config is None, using default Blt patcher config")
        elif isinstance(self.patcher_config, dict):
            self.patcher_config.setdefault("initializer_range", self.initializer_range)
            self.patcher_config = BltPatcherConfig(**self.patcher_config)

        if self.encoder_config is None:
            self.encoder_config = BltLocalEncoderConfig(initializer_range=self.initializer_range)
            logger.info("encoder_config is None, using default Blt encoder config")
        elif isinstance(self.encoder_config, dict):
            self.encoder_config.setdefault("initializer_range", self.initializer_range)
            self.encoder_config = BltLocalEncoderConfig(**self.encoder_config)

        if self.decoder_config is None:
            self.decoder_config = BltLocalDecoderConfig(initializer_range=self.initializer_range)
            logger.info("decoder_config is None, using default Blt decoder config")
        elif isinstance(self.decoder_config, dict):
            self.decoder_config.setdefault("initializer_range", self.initializer_range)
            self.decoder_config = BltLocalDecoderConfig(**self.decoder_config)

        if self.global_config is None:
            self.global_config = BltGlobalTransformerConfig(initializer_range=self.initializer_range)
            logger.info("global_config is None, using default Blt global config")
        elif isinstance(self.global_config, dict):
            self.global_config.setdefault("initializer_range", self.initializer_range)
            self.global_config = BltGlobalTransformerConfig(**self.global_config)

        # Determine if token embedding projection is needed based on dimension mismatch (7b)
        encoder_cross_output_size = self.encoder_config.hidden_size * self.cross_attn_k
        self.global_config.encoder_cross_output_size = (
            encoder_cross_output_size if encoder_cross_output_size != self.global_config.hidden_size else None
        )

        super().__post_init__(**kwargs)