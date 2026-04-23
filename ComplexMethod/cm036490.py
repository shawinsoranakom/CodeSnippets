def test_registry_model_property(model_arch, is_mm, init_cuda, score_type):
    model_info = ModelRegistry._try_inspect_model_cls(model_arch)
    assert model_info is not None

    assert model_info.supports_multimodal is is_mm
    assert model_info.score_type == score_type

    if init_cuda and current_platform.is_cuda_alike():
        assert not torch.cuda.is_initialized()

        ModelRegistry._try_load_model_cls(model_arch)
        if not torch.cuda.is_initialized():
            warnings.warn(
                "This model no longer initializes CUDA on import. "
                "Please test using a different one.",
                stacklevel=2,
            )