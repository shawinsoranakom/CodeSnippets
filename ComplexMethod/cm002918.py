def __post_init__(self, **kwargs):
        if self.vision_config is None:
            self.vision_config = Sam3VisionConfig()
        if isinstance(self.vision_config, dict):
            self.vision_config = Sam3VisionConfig(**self.vision_config)

        if self.text_config is None:
            self.text_config = CLIPTextConfig(
                **{
                    "vocab_size": 49408,
                    "hidden_size": 1024,
                    "intermediate_size": 4096,  # hidden_size * mlp_ratio (1024 * 4)
                    "projection_dim": 512,  # CLIP's internal projection dimension
                    "num_hidden_layers": 24,
                    "num_attention_heads": 16,
                    "max_position_embeddings": 32,
                    "hidden_act": "gelu",
                }
            )
        if isinstance(self.text_config, dict):
            self.text_config = CLIPTextConfig(**self.text_config)

        if self.geometry_encoder_config is None:
            self.geometry_encoder_config = Sam3GeometryEncoderConfig()
        if isinstance(self.geometry_encoder_config, dict):
            self.geometry_encoder_config = Sam3GeometryEncoderConfig(**self.geometry_encoder_config)

        if self.detr_encoder_config is None:
            self.detr_encoder_config = Sam3DETREncoderConfig()
        if isinstance(self.detr_encoder_config, dict):
            self.detr_encoder_config = Sam3DETREncoderConfig(**self.detr_encoder_config)

        if self.detr_decoder_config is None:
            self.detr_decoder_config = Sam3DETRDecoderConfig()
        if isinstance(self.detr_decoder_config, dict):
            self.detr_decoder_config = Sam3DETRDecoderConfig(**self.detr_decoder_config)

        if self.mask_decoder_config is None:
            self.mask_decoder_config = Sam3MaskDecoderConfig()
        if isinstance(self.mask_decoder_config, dict):
            self.mask_decoder_config = Sam3MaskDecoderConfig(**self.mask_decoder_config)

        super().__post_init__(**kwargs)