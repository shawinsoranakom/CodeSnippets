def test_vllm_config_explicit_overrides():
    """Test that explicit property overrides work correctly with callable defaults.

    When users explicitly set configuration properties, those values
    take precedence over callable defaults, across different models and
    optimization levels.
    """
    from vllm.config.compilation import PassConfig

    quantized_model = ModelConfig("RedHatAI/Llama-3.2-1B-FP8")
    moe_model = ModelConfig("deepseek-ai/DeepSeek-V2-Lite")
    regular_model = ModelConfig("Qwen/Qwen1.5-7B")

    # Explicit compilation mode override on O0 (where default is NONE)
    compilation_config = CompilationConfig(mode=CompilationMode.VLLM_COMPILE)
    config = VllmConfig(
        optimization_level=OptimizationLevel.O0,
        compilation_config=compilation_config,
    )
    assert config.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.NONE

    # Explicit pass config flags to override defaults
    pass_config = PassConfig(eliminate_noops=True, fuse_attn_quant=True)
    compilation_config = CompilationConfig(pass_config=pass_config)
    config = VllmConfig(
        optimization_level=OptimizationLevel.O0,
        compilation_config=compilation_config,
    )
    assert config.compilation_config.pass_config.eliminate_noops is True
    assert config.compilation_config.pass_config.fuse_attn_quant is True

    # Explicit cudagraph mode override on quantized model at O2
    pass_config = PassConfig(enable_qk_norm_rope_fusion=True)
    compilation_config = CompilationConfig(
        cudagraph_mode=CUDAGraphMode.NONE, pass_config=pass_config
    )
    config = VllmConfig(
        model_config=quantized_model,
        optimization_level=OptimizationLevel.O2,
        compilation_config=compilation_config,
    )
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.NONE
    assert config.compilation_config.pass_config.enable_qk_norm_rope_fusion is True
    # Mode should still use default for O2
    assert config.compilation_config.mode == CompilationMode.VLLM_COMPILE

    # Different optimization levels with same model
    config_o0 = VllmConfig(
        model_config=regular_model, optimization_level=OptimizationLevel.O0
    )
    config_o2 = VllmConfig(
        model_config=regular_model, optimization_level=OptimizationLevel.O2
    )
    assert config_o0.compilation_config.mode == CompilationMode.NONE
    assert config_o2.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert config_o0.compilation_config.cudagraph_mode == CUDAGraphMode.NONE
    assert (
        config_o2.compilation_config.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE
    )

    # Same optimization level across different model types
    config_moe_o2 = VllmConfig(
        model_config=moe_model, optimization_level=OptimizationLevel.O2
    )
    config_regular_o2 = VllmConfig(
        model_config=regular_model, optimization_level=OptimizationLevel.O2
    )
    config_quantized_o2 = VllmConfig(
        model_config=quantized_model, optimization_level=OptimizationLevel.O2
    )
    # All should have same base compilation settings at O2
    assert config_moe_o2.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert config_regular_o2.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert config_quantized_o2.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert (
        config_moe_o2.compilation_config.cudagraph_mode
        == CUDAGraphMode.FULL_AND_PIECEWISE
    )
    assert (
        config_regular_o2.compilation_config.cudagraph_mode
        == CUDAGraphMode.FULL_AND_PIECEWISE
    )

    # Override one field but not others
    pass_config = PassConfig(eliminate_noops=False)
    compilation_config = CompilationConfig(pass_config=pass_config)
    config = VllmConfig(
        model_config=regular_model,
        optimization_level=OptimizationLevel.O2,
        compilation_config=compilation_config,
    )
    # Explicit override should be respected
    assert config.compilation_config.pass_config.eliminate_noops is False
    # Other fields should still use defaults
    assert config.compilation_config.mode == CompilationMode.VLLM_COMPILE
    assert config.compilation_config.cudagraph_mode == CUDAGraphMode.FULL_AND_PIECEWISE