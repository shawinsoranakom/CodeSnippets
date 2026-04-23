def _prepare_cache_for_generation(
        self,
        generation_config: GenerationConfig,
        model_kwargs: dict,
        generation_mode: GenerationMode,
        batch_size: int,
        max_cache_length: int,
    ) -> bool:
        """Override cache preparation to support T5Gemma2-specific EncoderDecoder Cache."""

        # Build cache and past_key_values structure first and then override as needed.
        super()._prepare_cache_for_generation(
            generation_config,
            model_kwargs,
            generation_mode,
            batch_size,
            max_cache_length,
        )

        # If use_cache is False, do not prepare the cache.
        if generation_config.use_cache is False:
            return

        cache_implementation = generation_config.cache_implementation
        if cache_implementation is None:
            offload_cache = False
        else:
            offload_cache = "offloaded" in generation_config.cache_implementation

        # Main change: use full cache for cross-attention.
        cross_attn_config = copy.deepcopy(self.config.get_text_config(decoder=True))

        # cross-attention does not use sliding window
        del cross_attn_config.sliding_window
        del cross_attn_config.layer_types

        cross_attn_cache_kwargs = {
            "config": cross_attn_config,
            "offloading": offload_cache,
        }

        past_key_values = model_kwargs.get("past_key_values")
        if past_key_values is not None:
            if not isinstance(past_key_values, EncoderDecoderCache):
                raise ValueError(
                    "The `past_key_values` in `model_kwargs` must be of type `EncoderDecoderCache` for T5Gemma2 model."
                )

            # Cache already established, no need to re-initialize.
            if len(past_key_values.is_updated) > 0 and past_key_values.is_updated.get(0):
                return

            cross_attn_cls = type(past_key_values.cross_attention_cache)
            if cross_attn_cls == StaticCache:
                cross_attn_cache_kwargs["max_cache_len"] = model_kwargs["encoder_outputs"][0].shape[1]
            # Update cross-attention cache only (switch from sliding_window to full).
            past_key_values.cross_attention_cache = cross_attn_cls(**cross_attn_cache_kwargs)
        else:
            # Initialize new cache.
            model_kwargs["past_key_values"] = EncoderDecoderCache(
                DynamicCache(
                    **{
                        "config": self.config.get_text_config(decoder=True),
                        "offloading": offload_cache,
                    }
                ),  # self-attention cache
                DynamicCache(),  # cross-attention cache
            )

        if hasattr(self, "_cache") and self._cache is not None:
            if not isinstance(self._cache, EncoderDecoderCache):
                raise ValueError("The internal cache must be of type `EncoderDecoderCache` for T5Gemma2 model.")

            self._cache = model_kwargs["past_key_values"]