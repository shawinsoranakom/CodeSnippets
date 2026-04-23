def __post_init__(self, **kwargs):
        self.memory_attention_rope_feat_sizes = (
            [64, 64] if self.memory_attention_rope_feat_sizes is None else self.memory_attention_rope_feat_sizes
        )

        if isinstance(self.vision_config, dict):
            self.vision_config["model_type"] = self.vision_config.get("model_type", "sam2_vision_model")
            self.vision_config = CONFIG_MAPPING[self.vision_config["model_type"]](**self.vision_config)
        elif self.vision_config is None:
            self.vision_config = CONFIG_MAPPING["sam2_vision_model"]()

        if isinstance(self.prompt_encoder_config, dict):
            self.prompt_encoder_config = Sam2VideoPromptEncoderConfig(**self.prompt_encoder_config)
        elif self.prompt_encoder_config is None:
            self.prompt_encoder_config = Sam2VideoPromptEncoderConfig()

        if isinstance(self.mask_decoder_config, dict):
            self.mask_decoder_config = Sam2VideoPromptEncoderConfig(**self.mask_decoder_config)
        elif self.mask_decoder_config is None:
            self.mask_decoder_config = Sam2VideoMaskDecoderConfig()

        super().__post_init__(**kwargs)