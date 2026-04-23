def _test_processing_correctness(
    model_id_or_arch: str,
    hit_rate: float,
    num_batches: int,
    simplify_rate: float,
):
    if model_id_or_arch in HF_EXAMPLE_MODELS.get_supported_archs():
        # Use model architecture to get the default model id
        model_info = HF_EXAMPLE_MODELS.get_hf_info(model_id_or_arch)
        model_id = model_info.default
    else:
        model_info = HF_EXAMPLE_MODELS.find_hf_info(model_id_or_arch)
        model_id = model_id_or_arch
    model_info.check_available_online(on_fail="skip")
    model_info.check_transformers_version(
        on_fail="skip",
        check_max_version=False,
        check_version_reason="vllm",
    )

    model_config = ModelConfig(
        model_id,
        tokenizer=model_info.tokenizer or model_id,
        tokenizer_mode=model_info.tokenizer_mode,
        revision=model_info.revision,
        trust_remote_code=model_info.trust_remote_code,
        hf_overrides=model_info.hf_overrides,
        skip_tokenizer_init=model_info.require_embed_inputs,
        enable_prompt_embeds=model_info.require_embed_inputs,
        enable_mm_embeds=model_info.require_embed_inputs,
        enforce_eager=model_info.enforce_eager,
        dtype=model_info.dtype,
    )
    # Ensure that the cache can fit all of the data
    # (set after because ModelConfig would set it to 0 for encoder-decoder models)
    model_config.multimodal_config.mm_processor_cache_gb = 2048

    model_cls = MULTIMODAL_REGISTRY._get_model_cls(model_config)
    factories = model_cls._processor_factory
    ctx = InputProcessingContext(
        model_config,
        tokenizer=cached_tokenizer_from_config(model_config),
    )
    cache = MultiModalProcessorOnlyCache(model_config)

    processing_info = factories.info(ctx)
    supported_mm_limits = processing_info.get_supported_mm_limits()
    # Keep integer limits for local data generation
    limit_mm_per_prompt_ints = {
        modality: 3 if limit is None else limit
        for modality, limit in supported_mm_limits.items()
    }

    def _to_dummy_options(modality: str, count: int) -> BaseDummyOptions:
        if modality == "video":
            return VideoDummyOptions(count=count)
        if modality == "image":
            return ImageDummyOptions(count=count)
        if modality == "audio":
            return AudioDummyOptions(count=count)
        return BaseDummyOptions(count=count)

    # Assign normalized DummyOptions to the model config
    model_config.get_multimodal_config().limit_per_prompt = {
        modality: _to_dummy_options(modality, count)
        for modality, count in limit_mm_per_prompt_ints.items()
    }

    baseline_processor = factories.build_processor(ctx, cache=None)
    cached_processor = factories.build_processor(ctx, cache=cache)

    rng = np.random.RandomState(0)

    # GLM-ASR requires a minimum audio length of 70ms
    min_audio_len = 512 if model_config.hf_config.model_type != "glmasr" else 1120
    input_to_hit = {
        "image": Image.new("RGB", size=(128, 128)),
        "video": np.zeros((4, 128, 128, 3), dtype=np.uint8),
        "audio": (np.zeros((min_audio_len,)), 16000),
        "vision_chunk": {"type": "image", "image": Image.new("RGB", size=(128, 128))},
    }
    input_factory = {
        "image": partial(random_image, rng, min_wh=128, max_wh=256),
        "video": partial(
            random_video, rng, min_frames=2, max_frames=16, min_wh=128, max_wh=256
        ),
        "audio": partial(
            random_audio,
            rng,
            min_len=min_audio_len,
            max_len=min_audio_len + 512,
            sr=16000,
        ),
        "vision_chunk": partial(
            random_vision_chunk, rng, min_wh=128, max_wh=256, min_frames=1, max_frames=1
        ),
    }

    for batch_idx in range(num_batches):
        mm_data = {
            k: [
                (input_to_hit[k] if rng.rand() < hit_rate else input_factory[k]())
                for _ in range(rng.randint(limit + 1))
            ]
            for k, limit in limit_mm_per_prompt_ints.items()
        }

        # Drop unnecessary keys and test single -> multi conversion
        if rng.rand() < simplify_rate:
            for k in list(mm_data.keys()):
                if not mm_data[k]:
                    del mm_data[k]
                elif len(mm_data[k]) == 1:
                    mm_data[k] = mm_data[k][0]

        _test_processing_correctness_one(
            model_config,
            mm_data,
            baseline_processor,
            cached_processor,
            batch_idx,
        )