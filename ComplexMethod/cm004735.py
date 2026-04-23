def __post_init__(self, **kwargs):
        self.memory_attention_rope_feat_sizes = (
            [72, 72] if self.memory_attention_rope_feat_sizes is None else self.memory_attention_rope_feat_sizes
        )

        if isinstance(self.vision_config, dict):
            self.vision_config["model_type"] = self.vision_config.get("model_type", "sam3_vision_model")
            self.vision_config = CONFIG_MAPPING[self.vision_config["model_type"]](**self.vision_config)
        elif self.vision_config is None:
            self.vision_config = CONFIG_MAPPING["sam3_vision_model"](
                backbone_feature_sizes=[[288, 288], [144, 144], [72, 72]]
            )

        if isinstance(self.prompt_encoder_config, dict):
            self.prompt_encoder_config = Sam3TrackerVideoPromptEncoderConfig(**self.prompt_encoder_config)
        elif self.prompt_encoder_config is None:
            self.prompt_encoder_config = Sam3TrackerVideoPromptEncoderConfig()

        if isinstance(self.mask_decoder_config, dict):
            self.mask_decoder_config = Sam3TrackerVideoMaskDecoderConfig(**self.mask_decoder_config)
        elif self.mask_decoder_config is None:
            self.mask_decoder_config = Sam3TrackerVideoMaskDecoderConfig()

        self.image_size = kwargs.pop("image_size", 1008)
        super().__post_init__(**kwargs)