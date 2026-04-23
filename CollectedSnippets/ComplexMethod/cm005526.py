def _extract_generation_mode_kwargs(
        self,
        custom_generate,
        kwargs,
        synced_gpus,
        assistant_model,
        streamer,
    ) -> dict[str, Any]:
        """
        Extracts and returns the generation mode related keyword arguments from the provided kwargs.
        """
        generation_mode_kwargs = {
            "tokenizer": kwargs.pop("tokenizer", None),
            "assistant_tokenizer": kwargs.pop("assistant_tokenizer", None),
            "assistant_model": assistant_model,
            "streamer": streamer,
        }
        world_size = dist.get_world_size() if dist.is_available() and dist.is_initialized() else 1  # type: ignore
        generation_mode_kwargs["synced_gpus"] = (
            (is_deepspeed_zero3_enabled() or is_fsdp_managed_module(self)) and world_size > 1
            if synced_gpus is None
            else synced_gpus
        )
        generation_mode_kwargs = {k: v for k, v in generation_mode_kwargs.items() if v is not None}
        # Custom_generate callables can have their own set of arguments
        # To extract them, we compare the signature with the standard _sample method
        if isinstance(custom_generate, Callable):
            usual_mode_kwargs = inspect.signature(GenerationMixin._sample).parameters.keys()
            custom_generate_kwargs = inspect.signature(custom_generate).parameters.keys()
            new_custom_keys = custom_generate_kwargs - usual_mode_kwargs
            generation_mode_kwargs = {k: kwargs.pop(k) for k in new_custom_keys if k in kwargs}
        return generation_mode_kwargs