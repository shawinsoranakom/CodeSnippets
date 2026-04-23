def test_registry_imports(model_arch):
    # Skip if transformers version is incompatible
    model_info = HF_EXAMPLE_MODELS.get_hf_info(model_arch)
    model_info.check_transformers_version(
        on_fail="skip",
        check_max_version=False,
        check_version_reason="vllm",
    )
    # Ensure all model classes can be imported successfully
    model_cls = ModelRegistry._try_load_model_cls(model_arch)
    assert model_cls is not None

    if model_arch in _SPECULATIVE_DECODING_MODELS:
        return  # Ignore these models which do not have a unified format

    if model_arch in _TEXT_GENERATION_MODELS or model_arch in _MULTIMODAL_MODELS:
        assert is_text_generation_model(model_cls)

    # All vLLM models should be convertible to a pooling model
    assert is_pooling_model(as_seq_cls_model(model_cls))
    assert is_pooling_model(as_embedding_model(model_cls))

    if model_arch in _MULTIMODAL_MODELS:
        assert supports_multimodal(model_cls)