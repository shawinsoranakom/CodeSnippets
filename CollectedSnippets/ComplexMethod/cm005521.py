def _prepare_generation_config(
        self: "GenerativePreTrainedModel",
        generation_config: GenerationConfig | None,
        **kwargs: Any,
    ) -> tuple[GenerationConfig, dict]:
        """
        Prepares the base generation config, then applies any generation configuration options from kwargs. This
        function handles retrocompatibility with respect to configuration files.
        """
        # parameterization priority:
        # user-defined kwargs or `generation_config` > `self.generation_config` > global default values
        # TODO (joao): per-model generation config classes.

        generation_config_provided = generation_config is not None
        if generation_config is None:
            # Users may modify `model.config` to control generation. This is a legacy behavior and is not supported anymore
            if len(self.config._get_generation_parameters()) > 0:
                raise ValueError(
                    "You have modified the pretrained model configuration to control generation "
                    f"We detected the following values set - {self.config._get_generation_parameters()}. "
                    "This strategy to control generation is not supported anymore. Please use and modify `model.generation_config` "
                    "(see https://huggingface.co/docs/transformers/generation_strategies#default-text-generation-configuration )",
                )
            generation_config = GenerationConfig()

        # `torch.export.export` usually raises an exception if it is called
        # with ``strict=True``. deepcopy can only be processed if ``strict=False``.
        generation_config = copy.deepcopy(generation_config)

        # First set values from the loaded `self.generation_config`, then set default values (BC)
        #
        # Only update values that are `None`, i.e. these values were not explicitly set by users to `generate()`,
        # or values that are not present in the current config, i.e. custom entries that were set via `**kwargs`.
        # Thus we use the specific kwargs `defaults_only=True` (`None` values only) and `allow_custom_entries=True`
        # (custom entries are carried over).
        global_defaults = self.generation_config._get_default_generation_params()
        generation_config.update(**self.generation_config.to_dict(), defaults_only=True, allow_custom_entries=True)
        generation_config.update(**global_defaults, defaults_only=True)

        # Finally, if there are any kwargs, update config with it -> highest priority at the end
        model_kwargs = generation_config.update(**kwargs)

        # Related to #40039: prior to this PR, models with sliding window attention were forced to have
        # `cache_implementation="hybrid"` (the static sliding window cache). For these models, we now want to use
        # the dynamic sliding window cache by default, so we UNSET `cache_implementation` if it is a default value.
        # (if we're inside this branch, then it is because we're using default values from the Hub)
        if generation_config.cache_implementation == "hybrid":
            generation_config.cache_implementation = None

        # It doesn't make sense to allow kwargs and `generation_config`, that should be mutually exclusive
        if generation_config_provided and set(kwargs.keys()) - set(model_kwargs.keys()):
            generation_kwargs = set(kwargs.keys()) - set(model_kwargs.keys())
            logger.warning_once(
                f"Passing `generation_config` together with generation-related "
                f"arguments=({generation_kwargs}) is deprecated and will be removed in future versions. "
                "Please pass either a `generation_config` object OR all generation "
                "parameters explicitly, but not both.",
            )

        # Finally keep output_xxx args in `model_kwargs` so it can be passed to `forward`
        output_attentions = generation_config.output_attentions
        output_hidden_states = generation_config.output_hidden_states
        model_kwargs.update({"output_attentions": output_attentions} if output_attentions else {})
        model_kwargs.update({"output_hidden_states": output_hidden_states} if output_hidden_states else {})

        return generation_config, model_kwargs