def _prepare_generation_config(
        self, generation_config: GenerationConfig | None, **kwargs: Any
    ) -> tuple[GenerationConfig, dict]:
        """
        This method overrides [~generation.utils.GenerationMixin._prepare_generation_config].
        It ensures that the depth decoder generation config is initialized and that passed args as depth_decoder_* are properly handled.
        """
        # extract depth decoder kwargs and remove them from the main kwargs
        depth_decoder_kwargs = {
            k[len("depth_decoder_") :]: v for k, v in kwargs.items() if k.startswith("depth_decoder_")
        }

        # remove the depth decoder keys from the original kwargs
        kwargs = {k: v for k, v in kwargs.items() if not k.startswith("depth_decoder_")}

        # initialize the generation config
        generation_config, model_kwargs = super()._prepare_generation_config(generation_config, **kwargs)
        self.depth_decoder.generation_config.update(**depth_decoder_kwargs)

        # ensure the depth decoder generation config is valid
        depth_decoder_min_new_tokens = getattr(self.depth_decoder.generation_config, "min_new_tokens") or (
            self.config.num_codebooks - 1
        )
        depth_decoder_max_new_tokens = getattr(self.depth_decoder.generation_config, "max_new_tokens") or (
            self.config.num_codebooks - 1
        )

        if {depth_decoder_min_new_tokens, depth_decoder_max_new_tokens} != {self.config.num_codebooks - 1}:
            raise ValueError(
                f"depth_decoder_generation_config's min_new_tokens ({depth_decoder_min_new_tokens}) and max_new_tokens ({depth_decoder_max_new_tokens}) must be equal to self.config.num_codebooks - 1 ({self.config.num_codebooks - 1})"
            )
        elif self.depth_decoder.generation_config.return_dict_in_generate:
            logger.warning(
                "depth_decoder_generation_config.return_dict_in_generate is set to True, but this will be ignored as the depth decoder model does not return a dictionary in generate"
            )
            self.depth_decoder.generation_config.return_dict_in_generate = False

        self.depth_decoder.generation_config.min_new_tokens = depth_decoder_min_new_tokens
        self.depth_decoder.generation_config.max_new_tokens = depth_decoder_max_new_tokens

        # Monkey patch the get_generation_mode method to support CSM model
        original_get_generation_mode = generation_config.get_generation_mode

        def patched_get_generation_mode(assistant_model=None):
            generation_mode = original_get_generation_mode(assistant_model)
            if generation_mode not in [GenerationMode.GREEDY_SEARCH, GenerationMode.SAMPLE]:
                raise ValueError(
                    f"Generation mode {generation_mode} is not supported for CSM model. Please set generation parameters to use greedy or sampling generation."
                )

            return generation_mode

        generation_config.get_generation_mode = patched_get_generation_mode

        return generation_config, model_kwargs