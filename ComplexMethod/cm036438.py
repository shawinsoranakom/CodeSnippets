def test_compilation_config_mode_validator():
    """Test that CompilationConfig.mode field validator converts strings to integers."""
    from vllm.config.compilation import CompilationConfig, CompilationMode

    config = CompilationConfig(mode=0)
    assert config.mode == CompilationMode.NONE

    config = CompilationConfig(mode=3)
    assert config.mode == CompilationMode.VLLM_COMPILE

    config = CompilationConfig(mode="NONE")
    assert config.mode == CompilationMode.NONE

    config = CompilationConfig(mode="STOCK_TORCH_COMPILE")
    assert config.mode == CompilationMode.STOCK_TORCH_COMPILE

    config = CompilationConfig(mode="DYNAMO_TRACE_ONCE")
    assert config.mode == CompilationMode.DYNAMO_TRACE_ONCE

    config = CompilationConfig(mode="VLLM_COMPILE")
    assert config.mode == CompilationMode.VLLM_COMPILE

    config = CompilationConfig(mode="none")
    assert config.mode == CompilationMode.NONE

    config = CompilationConfig(mode="vllm_compile")
    assert config.mode == CompilationMode.VLLM_COMPILE

    with pytest.raises(ValidationError, match="Invalid compilation mode"):
        CompilationConfig(mode="INVALID_MODE")