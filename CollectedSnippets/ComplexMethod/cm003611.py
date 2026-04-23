def __post_init__(self, **kwargs):
        if isinstance(self.vision_config, dict):
            self.vision_config["model_type"] = self.vision_config.get("model_type", "siglip_vision_model")
            self.vision_config = CONFIG_MAPPING[self.vision_config["model_type"]](**self.vision_config)
        elif self.vision_config is None:
            self.vision_config = CONFIG_MAPPING["siglip_vision_model"](
                hidden_size=1152,
                intermediate_size=4304,
                patch_size=14,
                image_size=384,
                num_hidden_layers=26,
                num_attention_heads=16,
                vision_use_head=False,
            )

        if isinstance(self.text_config, dict):
            self.text_config["model_type"] = self.text_config.get("model_type", "qwen2")
            self.text_config = CONFIG_MAPPING[self.text_config["model_type"]](**self.text_config)
        elif self.text_config is None:
            self.text_config = CONFIG_MAPPING["qwen2"]()

        self.image_grid_pinpoints = (
            self.image_grid_pinpoints
            if self.image_grid_pinpoints is not None
            else [
                [384, 384],
                [384, 768],
                [384, 1152],
                [384, 1536],
                [384, 1920],
                [384, 2304],
                [768, 384],
                [768, 768],
                [768, 1152],
                [768, 1536],
                [768, 1920],
                [768, 2304],
                [1152, 384],
                [1152, 768],
                [1152, 1152],
                [1152, 1536],
                [1152, 1920],
                [1152, 2304],
                [1536, 384],
                [1536, 768],
                [1536, 1152],
                [1536, 1536],
                [1536, 1920],
                [1536, 2304],
                [1920, 384],
                [1920, 768],
                [1920, 1152],
                [1920, 1536],
                [1920, 1920],
                [1920, 2304],
                [2304, 384],
                [2304, 768],
                [2304, 1152],
                [2304, 1536],
                [2304, 1920],
                [2304, 2304],
            ]
        )

        # The default value is `False` but this config is used with many model types
        # Attr `tie_word_embeddings` was saved in text config for those models, so we
        # need an ugly workaround and forward-pass the attr from text config
        if not self.tie_word_embeddings and self.text_config.tie_word_embeddings:
            self.tie_word_embeddings = self.text_config.tie_word_embeddings

        super().__post_init__(**kwargs)