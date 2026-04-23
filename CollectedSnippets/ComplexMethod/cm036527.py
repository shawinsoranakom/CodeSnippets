def test_model_tensor_schema(model_id: str):
    if model_id == "moonshotai/Kimi-K2.5":
        # FIXME(Isotr0py): Fix Kimi-K2.5's offline inference about vision chunks.
        pytest.skip(
            "Kimi-K2.5's offline inference has issues about vision chunks. Fix later."
        )

    model_info = HF_EXAMPLE_MODELS.find_hf_info(model_id)
    model_info.check_available_online(on_fail="skip")
    model_info.check_transformers_version(
        on_fail="skip",
        check_max_version=False,
        check_version_reason="vllm",
    )

    model_arch = next(
        arch for arch, info in HF_EXAMPLE_MODELS.hf_models.items() if info == model_info
    )

    hf_overrides_fn = partial(
        dummy_hf_overrides,
        model_arch=model_arch,
        exist_overrides=model_info.hf_overrides,
    )

    # ROCm: Detect if model uses AWQ quantization and set appropriate dtype
    if "awq" in model_id.lower() and current_platform.is_rocm():
        dtype = "float16"
    else:
        dtype = model_info.dtype

    model_config = ModelConfig(
        model_id,
        tokenizer=model_info.tokenizer or model_id,
        tokenizer_mode=model_info.tokenizer_mode,
        revision=model_info.revision,
        trust_remote_code=model_info.trust_remote_code,
        hf_overrides=hf_overrides_fn,
        skip_tokenizer_init=model_info.require_embed_inputs,
        enable_prompt_embeds=model_info.require_embed_inputs,
        enable_mm_embeds=model_info.require_embed_inputs,
        enforce_eager=model_info.enforce_eager,
        dtype=dtype,
    )

    model_cls = MULTIMODAL_REGISTRY._get_model_cls(model_config)
    assert supports_multimodal(model_cls)

    factories = model_cls._processor_factory

    inputs_parse_methods = []
    for attr_name in dir(model_cls):
        attr = getattr(model_cls, attr_name)
        if hasattr(attr, "__annotations__"):
            return_type = attr.__annotations__.get("return", None)
            if return_type is not None and "Input" in str(return_type):
                inputs_parse_methods.append(attr_name)

    if not any(inputs_parse_methods):
        pytest.skip(f"{model_arch} does not support tensor schema validation.")

    ctx = InputProcessingContext(
        model_config,
        tokenizer=cached_tokenizer_from_config(model_config),
    )
    processing_info = factories.info(ctx)
    supported_mm_limits = processing_info.get_supported_mm_limits()
    limit_mm_per_prompt = {
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

    model_config.get_multimodal_config().limit_per_prompt = {
        modality: _to_dummy_options(modality, count)
        for modality, count in limit_mm_per_prompt.items()
    }
    processor = factories.build_processor(ctx, cache=None)

    with initialize_dummy_model(model_cls, model_config) as model:
        for modality, _, mm_kwargs in create_batched_mm_kwargs(model_config, processor):
            for method_name in inputs_parse_methods:
                print(
                    f"Testing `{method_name}` with modality={modality} "
                    f"and mm_kwargs{list(mm_kwargs.keys())}"
                )
                getattr(model, method_name)(modality=modality, **mm_kwargs)