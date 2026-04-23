def __post_init__(self, **kwargs):
        for sub_config_key in self.sub_configs:
            sub_config = getattr(self, sub_config_key)

            if sub_config is None:
                sub_config = CONFIG_MAPPING["dinov2"](image_size=self.patch_size)
                logger.info(
                    f"`{sub_config_key}` is `None`. Initializing `{sub_config_key}` with the `Dinov2Config` "
                    f"with default values except `{sub_config_key}.image_size` is set to `config.patch_size`."
                )
            elif isinstance(sub_config, dict):
                sub_config = deepcopy(sub_config)
                if "model_type" not in sub_config:
                    raise KeyError(
                        f"The `model_type` key is missing in the `{sub_config_key}` dictionary. Please provide the model type."
                    )
                elif sub_config["model_type"] not in CONFIG_MAPPING:
                    raise ValueError(
                        f"The model type `{sub_config['model_type']}` in `{sub_config_key}` is not supported. Please provide a valid model type."
                    )
                image_size = sub_config.get("image_size")
                if image_size != self.patch_size:
                    logger.info(
                        f"The `image_size` in `{sub_config_key}` is set to `{image_size}`, "
                        f"but it does not match the required `patch_size` of `{self.patch_size}`. "
                        f"Updating `image_size` to `{self.patch_size}` for consistency. "
                        f"Ensure that `image_size` aligns with `patch_size` in the configuration."
                    )
                    sub_config.update({"image_size": self.patch_size})
                sub_config = CONFIG_MAPPING[sub_config["model_type"]](**sub_config)
            elif isinstance(sub_config, PreTrainedConfig):
                image_size = getattr(sub_config, "image_size", None)
                if image_size != self.patch_size:
                    raise ValueError(
                        f"`config.{sub_config_key}.image_size={image_size}` should match `config.patch_size={self.patch_size}`."
                    )
            else:
                raise TypeError(
                    f"Invalid type for `sub_config`. Expected `PreTrainedConfig`, `dict`, or `None`, but got {type(sub_config)}."
                )

            setattr(self, sub_config_key, sub_config)

        super().__post_init__(**kwargs)