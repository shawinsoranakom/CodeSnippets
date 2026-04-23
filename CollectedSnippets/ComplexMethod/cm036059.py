def test_vllm_config_defaults(model_id, compilation_config, optimization_level):
    """Test that optimization-level defaults are correctly applied."""

    model_config = None
    if model_id is not None:
        model_config = ModelConfig(model_id)
        vllm_config = VllmConfig(
            model_config=model_config,
            compilation_config=compilation_config,
            optimization_level=optimization_level,
        )
    else:
        vllm_config = VllmConfig(
            compilation_config=compilation_config,
            optimization_level=optimization_level,
        )
    # Use the global optimization level defaults
    default_config = OPTIMIZATION_LEVEL_TO_CONFIG[optimization_level]

    # Verify pass_config defaults (nested under compilation_config)
    pass_config_dict = default_config["compilation_config"]["pass_config"]
    for pass_k, pass_v in pass_config_dict.items():
        actual = getattr(vllm_config.compilation_config.pass_config, pass_k)
        expected = pass_v(vllm_config) if callable(pass_v) else pass_v
        assert actual == expected, (
            f"pass_config.{pass_k}: expected {expected}, got {actual}"
        )

    # Verify other compilation_config defaults
    compilation_config_dict = default_config["compilation_config"]
    for k, v in compilation_config_dict.items():
        if k == "pass_config":
            continue
        actual = getattr(vllm_config.compilation_config, k)
        expected = v(vllm_config) if callable(v) else v
        # On platforms without static graph support, __post_init__ forces
        # cudagraph_mode to NONE; expect that instead of the level default.
        if k == "cudagraph_mode" and not current_platform.support_static_graph_mode():
            expected = CUDAGraphMode.NONE
        assert actual == expected, (
            f"compilation_config.{k}: expected {expected}, got {actual}"
        )