def _build_generation_config(
        self, body: dict, model_generation_config: "GenerationConfig", use_cb: bool = False
    ) -> "GenerationConfig":
        """Build a GenerationConfig from shared params (temperature, top_p, seed, generation_config JSON).

        Subclasses should call ``super()._build_generation_config(...)`` then apply
        endpoint-specific params (``max_tokens``, ``max_output_tokens``, etc.).

        Args:
            body (`dict`):
                The raw request body.
            model_generation_config (`GenerationConfig`):
                The model's default generation config (will be deep-copied).
            use_cb (`bool`, *optional*, defaults to `False`):
                Whether continuous batching is active. If ``True``, disables the model's
                internal KV cache (CB manages its own paged cache).

        Returns:
            `GenerationConfig`: A new config with request-specific overrides applied.
        """
        from transformers import GenerationConfig

        if body.get("generation_config") is not None:
            generation_config = GenerationConfig(**json.loads(body["generation_config"]))
        else:
            generation_config = copy.deepcopy(model_generation_config)
            if generation_config.max_new_tokens is None or generation_config.max_new_tokens < 1024:
                generation_config.max_new_tokens = 1024

        if body.get("temperature") is not None:
            generation_config.temperature = float(body["temperature"])
            if float(body["temperature"]) == 0.0:
                generation_config.do_sample = False
        if body.get("top_p") is not None:
            generation_config.top_p = float(body["top_p"])
        if body.get("seed") is not None:
            set_torch_seed(body["seed"])

        # --compile flag: use static cache + torch.compile for faster decode
        if self.generation_state._compile and generation_config.cache_implementation is None:
            generation_config.cache_implementation = "static"

        # CB manages its own paged KV cache
        if use_cb:
            generation_config.use_cache = False

        # TODO: add prefix caching for the non-CB path (reuse KV cache across multi-turn conversations)

        return generation_config