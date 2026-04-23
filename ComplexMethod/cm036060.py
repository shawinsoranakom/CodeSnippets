def test_vllm_config_callable_defaults():
    """Test that callable defaults work in the config system.

    Verifies that lambdas in default configs can inspect VllmConfig properties
    (e.g., is_quantized, is_model_moe) to conditionally set optimization flags.
    """
    config_no_model = VllmConfig(optimization_level=OptimizationLevel.O2)

    # Callable that checks if model exists
    has_model = lambda cfg: cfg.model_config is not None
    assert has_model(config_no_model) is False

    # Test with quantized model
    quantized_model = ModelConfig("RedHatAI/Llama-3.2-1B-FP8")
    config_quantized = VllmConfig(
        model_config=quantized_model, optimization_level=OptimizationLevel.O2
    )
    enable_if_quantized = lambda cfg: (
        cfg.model_config is not None and cfg.model_config.is_quantized
    )
    assert enable_if_quantized(config_quantized) is True
    assert enable_if_quantized(config_no_model) is False

    # Test with MoE model
    moe_model = ModelConfig("deepseek-ai/DeepSeek-V2-Lite")
    config_moe = VllmConfig(
        model_config=moe_model, optimization_level=OptimizationLevel.O2
    )
    enable_if_sequential = lambda cfg: (
        cfg.model_config is not None and not cfg.model_config.is_moe
    )
    assert enable_if_sequential(config_moe) is False
    assert enable_if_sequential(config_quantized) is True