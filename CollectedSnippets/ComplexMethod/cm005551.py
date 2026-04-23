def from_model_config(cls, model_config: Union["PreTrainedConfig", dict]) -> "GenerationConfig":
        """
        Instantiates a [`GenerationConfig`] from a [`PreTrainedConfig`]. This function is useful to convert legacy
        [`PreTrainedConfig`] objects, which may contain generation parameters, into a stand-alone [`GenerationConfig`].

        Args:
            model_config (`PreTrainedConfig | dict`):
                The model config that will be used to instantiate the generation config.

        Returns:
            [`GenerationConfig`]: The configuration object instantiated from those parameters.
        """
        config_dict = model_config.to_dict() if not isinstance(model_config, dict) else model_config
        config_dict.pop("_from_model_config", None)

        # Removes all `None` from the model config dict -- this lets the generation config defaults to take hold
        config_dict = {key: value for key, value in config_dict.items() if value is not None}
        generation_config = cls.from_dict(config_dict, return_unused_kwargs=False, _from_model_config=True)

        # Special case: some models have generation attributes set in the decoder. Use them if still unset in the
        # generation config (which in turn is defined from the outer attributes of model config).
        if isinstance(model_config, dict):
            decoder_possible_text_config_names = ("decoder", "generator", "text_config")
            for text_config_name in decoder_possible_text_config_names:
                if text_config := model_config.get(text_config_name):
                    model_config = text_config
                    break
        else:
            model_config = model_config.get_text_config(decoder=True)
            model_config = model_config.to_dict()

        default_generation_config = GenerationConfig()
        for attr in generation_config.to_dict():
            is_unset = getattr(generation_config, attr) == getattr(default_generation_config, attr)
            if attr in model_config and is_unset:
                setattr(generation_config, attr, model_config[attr])

        # If any `output_...` flag is set to `True`, we ensure `return_dict_in_generate` is set to `True`.
        if not generation_config.return_dict_in_generate:
            if any(
                getattr(generation_config, extra_output_flag, False)
                for extra_output_flag in generation_config.extra_output_flags
            ):
                generation_config.return_dict_in_generate = True

        # Hash to detect whether the instance was modified
        generation_config._original_object_hash = hash(generation_config)
        return generation_config