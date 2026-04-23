def __post_init__(self, **kwargs):
        if isinstance(self.encoder_config, dict):
            self.encoder_config = DiaEncoderConfig(**self.encoder_config)
        if isinstance(self.decoder_config, dict):
            self.decoder_config = DiaDecoderConfig(**self.decoder_config)

        self.encoder_config = self.encoder_config if self.encoder_config is not None else DiaEncoderConfig()
        self.decoder_config = self.decoder_config if self.decoder_config is not None else DiaDecoderConfig()
        self.delay_pattern = (
            self.delay_pattern if self.delay_pattern is not None else [0, 8, 9, 10, 11, 12, 13, 14, 15]
        )

        # TODO: Remove token ID forwarding once the `nari-labs/Dia-1.6B` checkpoint is updated
        if self.pad_token_id is not None:
            logger.warning_once(
                "Passing `pad_token_id` to `DiaConfig` is deprecated. "
                "Please set it directly on `DiaDecoderConfig` instead."
            )
            self.decoder_config.pad_token_id = self.pad_token_id

        if self.eos_token_id is not None:
            logger.warning_once(
                "Passing `eos_token_id` to `DiaConfig` is deprecated. "
                "Please set it directly on `DiaDecoderConfig` instead."
            )
            self.decoder_config.eos_token_id = self.eos_token_id

        if self.bos_token_id is not None:
            logger.warning_once(
                "Passing `bos_token_id` to `DiaConfig` is deprecated. "
                "Please set it directly on `DiaDecoderConfig` instead."
            )
            self.decoder_config.bos_token_id = self.bos_token_id

        super().__post_init__(**kwargs)