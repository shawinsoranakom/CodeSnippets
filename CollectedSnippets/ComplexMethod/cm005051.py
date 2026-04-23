def __post_init__(self, **kwargs):
        if self.text_config is None:
            text_config = {}
            logger.info("`text_config` is `None`. Initializing the `FlavaTextConfig` with default values.")
        elif isinstance(self.text_config, FlavaTextConfig):
            text_config = self.text_config.to_dict()
        else:
            text_config = self.text_config

        if self.image_config is None:
            image_config = {}
            logger.info("`image_config` is `None`. initializing the `FlavaImageConfig` with default values.")
        elif isinstance(self.image_config, FlavaImageConfig):
            image_config = self.image_config.to_dict()
        else:
            image_config = self.image_config

        if self.multimodal_config is None:
            multimodal_config = {}
            logger.info("`multimodal_config` is `None`. Initializing the `FlavaMultimodalConfig` with default values.")
        elif isinstance(self.multimodal_config, FlavaMultimodalConfig):
            multimodal_config = self.multimodal_config.to_dict()
        else:
            multimodal_config = self.multimodal_config

        if self.image_codebook_config is None:
            image_codebook_config = {}
            logger.info(
                "`image_codebook_config` is `None`. initializing the `FlavaImageCodebookConfig` with default values."
            )
        elif isinstance(self.image_codebook_config, FlavaImageCodebookConfig):
            image_codebook_config = self.image_codebook_config.to_dict()
        else:
            image_codebook_config = self.image_codebook_config

        # If `_config_dict` exist, we use them for the backward compatibility.
        text_config_dict = kwargs.pop("text_config_dict", None)
        image_config_dict = kwargs.pop("image_config_dict", None)
        multimodal_config_dict = kwargs.pop("multimodal_config_dict", None)
        image_codebook_config_dict = kwargs.pop("image_codebook_config_dict", None)

        # Instead of simply assigning `[text|vision]_config_dict` to `[text|vision]_config`, we use the values in
        # `[text|vision]_config_dict` to update the values in `[text|vision]_config`. The values should be same in most
        # cases, but we don't want to break anything regarding `_config_dict` that existed before commit `8827e1b2`.
        if text_config_dict is not None:
            # This is the complete result when using `text_config_dict`.
            _text_config_dict = FlavaTextConfig(**text_config_dict).to_dict()

            # Give a warning if the values exist in both `_text_config_dict` and `text_config` but being different.
            for key, value in _text_config_dict.items():
                if key in text_config and value != text_config[key] and key != "transformers_version":
                    # If specified in `text_config_dict`
                    if key in text_config_dict:
                        message = (
                            f"`{key}` is found in both `text_config_dict` and `text_config` but with different values. "
                            f'The value `text_config_dict["{key}"]` will be used instead.'
                        )
                    # If inferred from default argument values (just to be super careful)
                    else:
                        message = (
                            f"`text_config_dict` is provided which will be used to initialize `FlavaTextConfig`. The "
                            f'value `text_config["{key}"]` will be overridden.'
                        )
                    logger.info(message)

            # Update all values in `text_config` with the ones in `_text_config_dict`.
            text_config.update(_text_config_dict)

        if image_config_dict is not None:
            # This is the complete result when using `image_config_dict`.
            _image_config_dict = FlavaImageConfig(**image_config_dict).to_dict()
            # convert keys to string instead of integer
            if "id2label" in _image_config_dict:
                _image_config_dict["id2label"] = {
                    str(key): value for key, value in _image_config_dict["id2label"].items()
                }

            # Give a warning if the values exist in both `_image_config_dict` and `image_config` but being different.
            for key, value in _image_config_dict.items():
                if key in image_config and value != image_config[key] and key != "transformers_version":
                    # If specified in `image_config_dict`
                    if key in image_config_dict:
                        message = (
                            f"`{key}` is found in both `image_config_dict` and `image_config` but with different "
                            f'values. The value `image_config_dict["{key}"]` will be used instead.'
                        )
                    # If inferred from default argument values (just to be super careful)
                    else:
                        message = (
                            f"`image_config_dict` is provided which will be used to initialize `FlavaImageConfig`. "
                            f'The value `image_config["{key}"]` will be overridden.'
                        )
                    logger.info(message)

            # Update all values in `image_config` with the ones in `_image_config_dict`.
            image_config.update(_image_config_dict)

        if multimodal_config_dict is not None:
            # This is the complete result when using `multimodal_config_dict`.
            _multimodal_config_dict = FlavaMultimodalConfig(**multimodal_config_dict).to_dict()

            # Give a warning if the values exist in both `_multimodal_config_dict` and `multimodal_config` but being
            # different.
            for key, value in _multimodal_config_dict.items():
                if key in multimodal_config and value != multimodal_config[key] and key != "transformers_version":
                    # If specified in `multimodal_config_dict`
                    if key in multimodal_config_dict:
                        message = (
                            f"`{key}` is found in both `multimodal_config_dict` and `multimodal_config` but with "
                            f'different values. The value `multimodal_config_dict["{key}"]` will be used instead.'
                        )
                    # If inferred from default argument values (just to be super careful)
                    else:
                        message = (
                            f"`multimodal_config_dict` is provided which will be used to initialize "
                            f'`FlavaMultimodalConfig`. The value `multimodal_config["{key}"]` will be overridden.'
                        )
                    logger.info(message)

            # Update all values in `multimodal_config` with the ones in `_multimodal_config_dict`.
            multimodal_config.update(_multimodal_config_dict)

        if image_codebook_config_dict is not None:
            # This is the complete result when using `image_codebook_config_dict`.
            _image_codebook_config_dict = FlavaImageCodebookConfig(**image_codebook_config_dict).to_dict()

            # Give a warning if the values exist in both `_image_codebook_config_dict` and `image_codebook_config` but
            # being different.
            for key, value in _image_codebook_config_dict.items():
                if (
                    key in image_codebook_config
                    and value != image_codebook_config[key]
                    and key != "transformers_version"
                ):
                    # If specified in `image_codebook_config_dict`
                    if key in image_codebook_config_dict:
                        message = (
                            f"`{key}` is found in both `image_codebook_config_dict` and `image_codebook_config` but "
                            f'with different values. The value `image_codebook_config_dict["{key}"]` will be used '
                            "instead."
                        )
                    # If inferred from default argument values (just to be super careful)
                    else:
                        message = (
                            f"`image_codebook_config_dict` is provided which will be used to initialize "
                            f'`FlavaImageCodebookConfig`. The value `image_codebook_config["{key}"]` will be overridden.'
                        )
                    logger.info(message)

            # Update all values in `image_codebook_config` with the ones in `_image_codebook_config_dict`.
            image_codebook_config.update(_image_codebook_config_dict)

        # Finally we can convert back our unified text/vision configs to `PretrainedConfig`
        self.text_config = FlavaTextConfig(**text_config)
        self.image_config = FlavaImageConfig(**image_config)
        self.multimodal_config = FlavaMultimodalConfig(**multimodal_config)
        self.image_codebook_config = FlavaImageCodebookConfig(**image_codebook_config)

        super().__post_init__(**kwargs)