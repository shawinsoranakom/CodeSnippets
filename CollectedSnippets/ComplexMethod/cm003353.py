def __post_init__(self, **kwargs):
        if self.perceiver_config is None:
            self.perceiver_config = Idefics2PerceiverConfig()
            logger.info("perciver_config is None, using default perceiver config")
        elif isinstance(self.perceiver_config, dict):
            self.perceiver_config = Idefics2PerceiverConfig(**self.perceiver_config)

        if self.vision_config is None:
            self.vision_config = Idefics2VisionConfig()
            logger.info("vision_config is None, using default vision config")
        elif isinstance(self.vision_config, dict):
            self.vision_config = Idefics2VisionConfig(**self.vision_config)

        if isinstance(self.text_config, dict):
            self.text_config["model_type"] = self.text_config.get("model_type", "mistral")
            self.text_config = CONFIG_MAPPING[self.text_config["model_type"]](**self.text_config)
        elif self.text_config is None:
            logger.info("text_config is None, using default text config")
            self.text_config = CONFIG_MAPPING["mistral"](
                max_position_embeddings=4096 * 8,
                rms_norm_eps=1e-5,
                # None in the original configuration_mistral, we set it to the unk_token_id
                pad_token_id=0,
            )

        if self.text_config.hidden_size != self.perceiver_config.hidden_size:
            self.perceiver_config.hidden_size = self.text_config.hidden_size
            self.perceiver_config.rms_norm_eps = self.text_config.rms_norm_eps
            logger.warning_once(
                "Perceiver config has a different `hidden_size` than text config, which means default values were used. "
                "In your model's config on the hub, add `hidden_size` and `rms_norm_eps` keys under the `perceiver_config` dict. "
            )

        super().__post_init__(**kwargs)