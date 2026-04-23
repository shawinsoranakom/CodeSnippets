def _prepare_generation_config(
        self,
        generation_config,
        **kwargs,
    ):
        # Check if user explicitly provided max_length or max_new_tokens BEFORE
        # the base class applies defaults
        user_set_max_length = kwargs.get("max_length") is not None or (
            generation_config is not None and generation_config.max_length is not None
        )
        user_set_max_new_tokens = kwargs.get("max_new_tokens") is not None or (
            generation_config is not None and generation_config.max_new_tokens is not None
        )

        generation_config, model_kwargs = GenerationMixin._prepare_generation_config(generation_config, **kwargs)

        input_features = model_kwargs.get("input_features")
        if input_features is not None and not isinstance(input_features, GeneratorType):
            audio_length = input_features.shape[-1]
            num_audio_tokens = math.ceil(audio_length / self.config.audio_length_per_tok)
            # Stash for use in _prepare_generated_length
            generation_config._num_audio_tokens = num_audio_tokens

            if not user_set_max_length and not user_set_max_new_tokens:
                # Default: generate exactly num_audio_tokens
                generation_config.max_length = num_audio_tokens
                generation_config.max_new_tokens = None
                generation_config._voxtral_set_max_length = True
            else:
                generation_config._voxtral_set_max_length = False

        elif isinstance(input_features, GeneratorType):
            # In streaming mode, generation length is controlled by stream exhaustion only
            generation_config.max_new_tokens = None
            generation_config.max_length = int(1e9)
            generation_config._voxtral_set_max_length = True

        return generation_config, model_kwargs