def _assert_model_config_methods(
    model_config, expected: dict, check_head_size: bool = True
):
    """Assert model_config methods return expected values."""
    assert model_config.architectures == expected["architectures"]
    assert model_config.get_vocab_size() == expected["vocab_size"]
    assert model_config.get_hidden_size() == expected["hidden_size"]
    assert model_config.get_total_num_kv_heads() == expected["total_num_kv_heads"]
    assert model_config.get_num_experts() == expected["num_experts"]
    assert (
        model_config.get_total_num_hidden_layers()
        == expected["total_num_hidden_layers"]
    )

    if check_head_size:
        assert model_config.get_head_size() == expected["head_size"]