def _prepare_static_cache(
        self: "GenerativePreTrainedModel", cache_implementation: str, batch_size: int, max_cache_len: int, model_kwargs
    ) -> Cache:
        """
        Sets a cache for `generate`, that will persist across calls. A new cache will only be initialized a
        new `generate` call requires a larger cache or uses a different batch size.

        Returns the resulting cache object.
        """
        offload_cache = "offloaded" in cache_implementation

        cache_to_check: StaticCache | None = None
        if hasattr(self, "_cache"):
            if isinstance(self._cache, EncoderDecoderCache):
                cache_to_check = self._cache.self_attention_cache
            elif isinstance(self._cache, StaticCache):
                cache_to_check = self._cache

        need_new_cache = (
            cache_to_check is None
            or cache_to_check.offloading != offload_cache
            or cache_to_check.max_batch_size != batch_size
            or cache_to_check.max_cache_len < max_cache_len
        )

        encoder_decoder_cache = getattr(self, "_cache", None)
        if isinstance(encoder_decoder_cache, EncoderDecoderCache):
            need_new_cache = (
                need_new_cache
                or encoder_decoder_cache.cross_attention_cache.max_cache_len
                != model_kwargs["encoder_outputs"][0].shape[1]
            )

        if need_new_cache:
            self_attention_cache_kwargs = {
                "config": self.config.get_text_config(decoder=True),
                "max_cache_len": max_cache_len,
                "offloading": offload_cache,
            }
            self._cache = StaticCache(**self_attention_cache_kwargs)
            if self.config.is_encoder_decoder:
                cross_attention_cache_kwargs = {
                    "config": self.config.get_text_config(decoder=True),
                    "max_cache_len": model_kwargs["encoder_outputs"][0].shape[1],
                    "offloading": offload_cache,
                }
                self._cache = EncoderDecoderCache(self._cache, StaticCache(**cross_attention_cache_kwargs))
        else:
            self._cache.reset()
        return self._cache