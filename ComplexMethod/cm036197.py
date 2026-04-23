def test_extract_hidden_states_config_preserves_vlm_text_config():
    """A real VLM config (LLaVA) with nested text_config must be preserved."""
    text_config = LlamaConfig(
        vocab_size=32000,
        hidden_size=128,
        intermediate_size=256,
        num_hidden_layers=2,
        num_attention_heads=8,
    )
    vlm_config = LlavaConfig(
        vision_config=CLIPVisionConfig(),
        text_config=text_config,
    )

    # Precondition: to_dict() flattens the nested config to a plain dict.
    assert isinstance(vlm_config.to_dict()["text_config"], dict)

    extract_config = ExtractHiddenStatesConfig(
        vlm_config,
        eagle_aux_hidden_state_layer_ids=[1, 2],
    )

    # The fix: text_config is still a PretrainedConfig, not a dict.
    assert isinstance(extract_config.text_config, LlamaConfig)

    extracted = get_hf_text_config(extract_config)
    assert extracted is extract_config.text_config
    assert extracted.num_attention_heads == text_config.num_attention_heads
    assert extracted.hidden_size == text_config.hidden_size

    # Serialization must still round-trip correctly.
    serialized = extract_config.to_dict()
    assert isinstance(serialized["text_config"], dict)
    assert serialized["text_config"]["num_attention_heads"] == (
        text_config.num_attention_heads
    )

    json_str = json.loads(extract_config.to_json_string())
    assert json_str["text_config"]["num_attention_heads"] == (
        text_config.num_attention_heads
    )