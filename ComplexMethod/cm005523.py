def _prepare_cache_for_generation(
        self: "GenerativePreTrainedModel",
        generation_config: GenerationConfig,
        model_kwargs: dict,
        generation_mode: GenerationMode,
        batch_size: int,
        max_cache_length: int,
    ) -> bool:
        """
        Prepares the cache for generation (if applicable), given `generate`'s parameterization. If a cache is
        instantiated, writes it to `model_kwargs`, under the name expected by the model.
        """

        # TODO @raushan, unify cache arg naming for all models
        is_linear_attn_cache = "mamba" in self.__class__.__name__.lower()
        cache_name = "past_key_values" if not is_linear_attn_cache else "cache_params"

        # Quick escape route 1: if the user specifies a cache, we only need to check for conflicting `generate` arguments
        user_defined_cache = model_kwargs.get(cache_name)
        if user_defined_cache is not None:
            if generation_config.cache_implementation is not None:
                raise ValueError(
                    f"Passing both `cache_implementation` (used to initialize certain caches) and `{cache_name}` (a "
                    "Cache object) is unsupported. Please use only one of the two."
                )
            if isinstance(user_defined_cache, tuple):
                raise ValueError(
                    "Passing a tuple of `past_key_values` is not supported anymore. Please use a `Cache` instance."
                )
            return

        # Quick escape route 2: if the user specifies no cache is to be used. (conflicting arguments are handled in
        # `generation_config.validate()`)
        if generation_config.use_cache is False:
            return

        # Quick escape route 3: model that supply it in `prepare_inputs_for_generation` (mamba, zamba, ...)
        if not self._supports_default_dynamic_cache():
            if generation_config.cache_implementation is not None:
                logger.warning_once(
                    "This model does not support `Cache` instances. `cache_implementation` (set to "
                    f"{generation_config.cache_implementation}) will be ignored.",
                )
            return

        # Otherwise we NEED to prepare a cache, based on `generation_config.cache_implementation`

        # Assisted decoding and contrastive search require cache rollback, which is incompatible with sliding layers.
        # To handle this, we skip passing the model config to DynamicCache (forcing a full-layer cache).
        # The "dynamic_full" option is a shortcut for generate() users to avoid sliding layers on their own.
        if generation_mode in (GenerationMode.ASSISTED_GENERATION, GenerationMode.CONTRASTIVE_SEARCH):
            if generation_config.cache_implementation is not None:
                logger.warning_once(
                    "An assistant model is provided, using a dynamic cache instead of a cache of type="
                    f"'{generation_config.cache_implementation}'."
                )
            generation_config.cache_implementation = "dynamic_full"

        dynamic_cache_kwargs = {}
        # linear attention models always need to pass the config, otherwise it will use an Attention cache for the LinearAttention layers
        is_linear_attention = any(
            x in ("mamba", "conv", "linear_attention")
            for x in (getattr(self.config.get_text_config(decoder=True), "layer_types", []) or [])
        )
        if generation_config.cache_implementation != "dynamic_full" or is_linear_attention:
            dynamic_cache_kwargs["config"] = self.config.get_text_config(decoder=True)

        if generation_config.cache_implementation == "offloaded":
            dynamic_cache_kwargs["offloading"] = True

        if generation_config.cache_implementation in ALL_STATIC_CACHE_IMPLEMENTATIONS:
            if generation_config.cache_implementation in DEPRECATED_STATIC_CACHE_IMPLEMENTATIONS:
                logger.warning_once(
                    f"Using `cache_implementation='{generation_config.cache_implementation}' is deprecated "
                    f"and will be removed in v5.13. Please only use one of {STATIC_CACHE_IMPLEMENTATIONS}, "
                    "and the layer structure will be inferred automatically."
                )
            model_kwargs[cache_name] = self._prepare_static_cache(
                cache_implementation=generation_config.cache_implementation,
                batch_size=max(generation_config.num_beams, generation_config.num_return_sequences) * batch_size,
                max_cache_len=max_cache_length,
                model_kwargs=model_kwargs,
            )
        elif generation_config.cache_implementation == "quantized":
            if self.config.is_encoder_decoder or not self._supports_default_dynamic_cache():
                raise ValueError(
                    "This model does not support the quantized cache. If you want your model to support quantized "
                    "cache, please open an issue and tag @zucchini-nlp."
                )

            cache_config = generation_config.cache_config if generation_config.cache_config is not None else {}
            cache_config.setdefault("config", self.config.get_text_config(decoder=True))
            backend = cache_config.pop("backend", "quanto")
            model_kwargs[cache_name] = QuantizedCache(backend=backend, **cache_config)
        # i.e. `cache_implementation` in [None, "dynamic", "offloaded", "dynamic_full"]
        # TODO: prepare linear cache from a single API, instead of creating in modeling code
        else:
            model_kwargs[cache_name] = DynamicCache(**dynamic_cache_kwargs)

        if (
            self.config.is_encoder_decoder
            and cache_name in model_kwargs
            and not isinstance(model_kwargs[cache_name], EncoderDecoderCache)
        ):
            model_kwargs[cache_name] = EncoderDecoderCache(
                model_kwargs[cache_name],  # self-attention cache
                DynamicCache(**dynamic_cache_kwargs),  # cross-attention cache
            )