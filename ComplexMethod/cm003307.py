def __post_init__(self, **kwargs):
        # Convert the keys and values of projector_patch_to_query_dict to integers
        # This ensures consistency even if they were provided as strings
        if self.projector_patch_to_query_dict is None:
            self.projector_patch_to_query_dict = {
                1225: 128,
                4900: 256,
            }
        self.projector_patch_to_query_dict = {int(k): int(v) for k, v in self.projector_patch_to_query_dict.items()}
        self.max_value_projector_patch_to_query_dict = max(self.projector_patch_to_query_dict.values())

        if isinstance(self.vision_config, dict):
            self.vision_config["model_type"] = "idefics3_vision"
            self.vision_config = CONFIG_MAPPING[self.vision_config["model_type"]](**self.vision_config)
        elif self.vision_config is None:
            self.vision_config = CONFIG_MAPPING["idefics3_vision"]()

        if isinstance(self.text_config, dict) and "model_type" in self.text_config:
            self.text_config = AriaTextConfig(**self.text_config)
        elif self.text_config is None:
            self.text_config = AriaTextConfig()

        super().__post_init__(**kwargs)