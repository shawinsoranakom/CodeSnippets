def __post_init__(self, **kwargs):
        if self.semantic_config is None:
            self.semantic_config = BarkSemanticConfig()
            logger.info("`semantic_config` is `None`. Initializing the `BarkSemanticConfig` with default values.")
        elif isinstance(self.semantic_config, dict):
            self.semantic_config = BarkSemanticConfig(**self.semantic_config)

        if self.coarse_acoustics_config is None:
            self.coarse_acoustics_config = BarkCoarseConfig()
            logger.info(
                "`coarse_acoustics_config` is `None`. Initializing the `BarkCoarseConfig` with default values."
            )
        elif isinstance(self.coarse_acoustics_config, dict):
            self.coarse_acoustics_config = BarkCoarseConfig(**self.coarse_acoustics_config)

        if self.fine_acoustics_config is None:
            self.fine_acoustics_config = BarkFineConfig()
            logger.info("`fine_acoustics_config` is `None`. Initializing the `BarkFineConfig` with default values.")
        elif isinstance(self.fine_acoustics_config, dict):
            self.fine_acoustics_config = BarkFineConfig(**self.fine_acoustics_config)

        if self.codec_config is None:
            self.codec_config = CONFIG_MAPPING["encodec"]()
            logger.info("`codec_config` is `None`. Initializing the `codec_config` with default values.")
        elif isinstance(self.codec_config, dict):
            codec_model_type = self.codec_config.get("model_type", "encodec")
            self.codec_config = CONFIG_MAPPING[codec_model_type](**self.codec_config)

        super().__post_init__(**kwargs)