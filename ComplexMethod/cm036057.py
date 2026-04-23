def test_rope_customization():
    TEST_ROPE_PARAMETERS = {
        "rope_theta": 16_000_000.0,
        "rope_type": "dynamic",
        "factor": 2.0,
    }
    LLAMA_ROPE_PARAMETERS = {"rope_theta": 500000.0, "rope_type": "default"}
    LONGCHAT_ROPE_PARAMETERS = {"rope_type": "linear", "factor": 8.0}

    llama_model_config = ModelConfig("meta-llama/Meta-Llama-3-8B-Instruct")
    assert (
        getattr(llama_model_config.hf_config, "rope_parameters", None)
        == LLAMA_ROPE_PARAMETERS
    )
    assert llama_model_config.max_model_len == 8192

    llama_model_config = ModelConfig(
        "meta-llama/Meta-Llama-3-8B-Instruct",
        hf_overrides={"rope_parameters": TEST_ROPE_PARAMETERS},
    )
    assert (
        getattr(llama_model_config.hf_config, "rope_parameters", None)
        == TEST_ROPE_PARAMETERS
    )
    assert llama_model_config.max_model_len == 16384

    longchat_model_config = ModelConfig("lmsys/longchat-13b-16k")
    # Check if LONGCHAT_ROPE_PARAMETERS entries are in longchat_model_config
    assert all(
        longchat_model_config.hf_config.rope_parameters.get(key) == value
        for key, value in LONGCHAT_ROPE_PARAMETERS.items()
    )
    assert longchat_model_config.max_model_len == 16384

    longchat_model_config = ModelConfig(
        "lmsys/longchat-13b-16k",
        hf_overrides={
            "rope_parameters": TEST_ROPE_PARAMETERS,
        },
    )
    assert (
        getattr(longchat_model_config.hf_config, "rope_parameters", None)
        == TEST_ROPE_PARAMETERS
    )
    assert longchat_model_config.max_model_len == 4096