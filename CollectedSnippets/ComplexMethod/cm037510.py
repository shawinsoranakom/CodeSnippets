def __init__(
        self,
        vllm_config: VllmConfig,
        mm_registry: MultiModalRegistry,
    ) -> None:
        super().__init__()

        self.model_config = model_config = vllm_config.model_config
        self.scheduler_config = scheduler_config = vllm_config.scheduler_config

        self.max_model_len = model_config.max_model_len
        self.max_num_reqs = scheduler_config.max_num_seqs

        with set_default_torch_num_threads():  # Avoid hang during startup
            cache = mm_registry.processor_only_cache_from_config(vllm_config)
            processor = mm_registry.create_processor(model_config, cache=cache)

            self.cache = cache
            self.processor = processor
            mm_config = model_config.get_multimodal_config()
            enable_mm_embeds = mm_config is not None and mm_config.enable_mm_embeds

            supported_mm_limits = processor.info.supported_mm_limits
            self.mm_limits = mm_limits = processor.info.allowed_mm_limits

            # Modalities that pass through the MM encoder tower
            tower_modalities = {
                modality
                for modality in supported_mm_limits
                if mm_limits.get(modality, 0) > 0
            }
            # Modalities that bypass the tower (pre-computed embeddings only)
            embed_only_modalities = {
                modality
                for modality in supported_mm_limits
                if enable_mm_embeds and mm_limits.get(modality, 0) == 0
            }

            active_modalities = tower_modalities | embed_only_modalities

            all_mm_max_toks_per_item = get_mm_max_toks_per_item(
                model_config,
                mm_registry,
                processor,
                mm_counts=dict.fromkeys(active_modalities, 1),
            )

        if embed_only_modalities:
            logger.info_once(
                "enable_mm_embeds is True; modalities handled as embedding-only: %s",
                tuple(embed_only_modalities),
            )

        # Some models (e.g., Qwen3Omni with use_audio_in_video=True) share
        # placeholders between modalities, so not all active modalities will
        # have their own entry in the returned dict. We filter to only include
        # modalities that have independent placeholder tokens.
        active_mm_max_toks_per_item = {
            modality: all_mm_max_toks_per_item[modality]
            for modality in active_modalities
            if modality in all_mm_max_toks_per_item
        }
        tower_mm_max_toks_per_item = {
            modality: active_mm_max_toks_per_item[modality]
            for modality in tower_modalities
            if modality in active_mm_max_toks_per_item
        }

        # Encoder budget is computed from all active modalities (including
        # embedding-only ones that need encoder cache space).
        encoder_compute_budget, encoder_cache_size = compute_mm_encoder_budget(
            scheduler_config,
            active_mm_max_toks_per_item,
        )

        self.encoder_compute_budget = encoder_compute_budget
        self.encoder_cache_size = encoder_cache_size

        mm_max_items_per_prompt = dict[str, int]()
        mm_max_items_per_batch = dict[str, int]()

        # Per-prompt/per-batch limits are only relevant for tower modalities
        # (embedding-only modalities don't go through the encoder tower).
        for modality, max_toks_per_item in tower_mm_max_toks_per_item.items():
            (
                mm_max_items_per_prompt[modality],
                mm_max_items_per_batch[modality],
            ) = self._get_max_items(modality, max_toks_per_item)

        self.mm_max_toks_per_item = tower_mm_max_toks_per_item
        self.mm_max_items_per_prompt: Mapping[str, int] = mm_max_items_per_prompt
        self.mm_max_items_per_batch: Mapping[str, int] = mm_max_items_per_batch