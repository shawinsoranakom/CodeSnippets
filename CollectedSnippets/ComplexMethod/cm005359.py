def __post_init__(self, **kwargs):
        if isinstance(self.vision_config, dict):
            self.vision_config["model_type"] = self.vision_config.get("model_type", "sam3_vision_model")
            self.vision_config = CONFIG_MAPPING[self.vision_config["model_type"]](**self.vision_config)
        elif self.vision_config is None:
            self.vision_config = CONFIG_MAPPING["sam3_vision_model"]()

        if self.text_config is None:
            self.text_config = Sam3LiteTextTextConfig()
        if isinstance(self.text_config, dict):
            self.text_config = Sam3LiteTextTextConfig(**self.text_config)

        if self.geometry_encoder_config is None:
            self.geometry_encoder_config = Sam3LiteTextGeometryEncoderConfig()
        if isinstance(self.geometry_encoder_config, dict):
            self.geometry_encoder_config = Sam3LiteTextGeometryEncoderConfig(**self.geometry_encoder_config)

        if self.detr_encoder_config is None:
            self.detr_encoder_config = Sam3LiteTextDETREncoderConfig()
        if isinstance(self.detr_encoder_config, dict):
            self.detr_encoder_config = Sam3LiteTextDETREncoderConfig(**self.detr_encoder_config)

        if self.detr_decoder_config is None:
            self.detr_decoder_config = Sam3LiteTextDETRDecoderConfig()
        if isinstance(self.detr_decoder_config, dict):
            self.detr_decoder_config = Sam3LiteTextDETRDecoderConfig(**self.detr_decoder_config)

        if self.mask_decoder_config is None:
            self.mask_decoder_config = Sam3LiteTextMaskDecoderConfig()
        if isinstance(self.mask_decoder_config, dict):
            self.mask_decoder_config = Sam3LiteTextMaskDecoderConfig(**self.mask_decoder_config)

        super().__post_init__(**kwargs)