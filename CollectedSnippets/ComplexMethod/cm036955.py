def _assert_model_arch_config(
    model_config, expected: dict, check_head_size: bool = True
):
    """Assert model_arch_config matches expected values."""
    model_arch_config = model_config.model_arch_config
    assert model_arch_config.architectures == expected["architectures"]
    assert model_arch_config.model_type == expected["model_type"]
    assert model_arch_config.text_model_type == expected["text_model_type"]
    assert model_arch_config.hidden_size == expected["hidden_size"]
    assert (
        model_arch_config.total_num_hidden_layers == expected["total_num_hidden_layers"]
    )
    assert (
        model_arch_config.total_num_attention_heads
        == expected["total_num_attention_heads"]
    )
    assert model_arch_config.vocab_size == expected["vocab_size"]
    assert model_arch_config.total_num_kv_heads == expected["total_num_kv_heads"]
    assert model_arch_config.num_experts == expected["num_experts"]
    assert model_arch_config.is_deepseek_mla == expected["is_deepseek_mla"]

    torch_dtype = ModelArchConfigConvertorBase.get_torch_dtype(
        model_config.hf_config,
        model_config.model,
        revision=model_config.revision,
        config_format="hf",
    )
    assert str(torch_dtype) == expected["dtype"]

    if check_head_size:
        assert model_arch_config.head_size == expected["head_size"]