def __post_init__(self, **kwargs):
        if self.thinker_config is None:
            self.thinker_config = Qwen3OmniMoeThinkerConfig()
            logger.info("thinker_config is None. Initializing thinker model with default values")
        elif isinstance(self.thinker_config, dict):
            self.thinker_config = Qwen3OmniMoeThinkerConfig(**self.thinker_config)

        if self.talker_config is None:
            self.talker_config = Qwen3OmniMoeTalkerConfig()
            logger.info("talker_config is None. Initializing talker model with default values")
        elif isinstance(self.talker_config, dict):
            self.talker_config = Qwen3OmniMoeTalkerConfig(**self.talker_config)

        if self.code2wav_config is None:
            self.code2wav_config = Qwen3OmniMoeCode2WavConfig()
            logger.info("code2wav_config is None. Initializing code2wav_config model with default values")
        elif isinstance(self.code2wav_config, dict):
            self.code2wav_config = Qwen3OmniMoeCode2WavConfig(**self.code2wav_config)

        if self.initializer_range is None:
            self.initializer_range = self.thinker_config.initializer_range

        super().__post_init__(**kwargs)