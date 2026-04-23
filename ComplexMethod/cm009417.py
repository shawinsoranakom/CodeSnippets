def test_model_data_to_profile_captures_all_models_dev_fields() -> None:
    """Test that all models.dev fields are captured in the profile."""
    model_data = {
        "id": "claude-opus-4-6",
        "name": "Claude Opus 4.6",
        "status": "deprecated",
        "release_date": "2025-06-01",
        "last_updated": "2025-07-01",
        "open_weights": False,
        "reasoning": True,
        "tool_call": True,
        "tool_choice": True,
        "structured_output": True,
        "attachment": True,
        "temperature": True,
        "limit": {"context": 200000, "output": 64000},
        "modalities": {
            "input": ["text", "image", "pdf"],
            "output": ["text"],
        },
    }
    profile = _model_data_to_profile(model_data)

    # Metadata
    assert profile["name"] == "Claude Opus 4.6"
    assert profile["status"] == "deprecated"
    assert profile["release_date"] == "2025-06-01"
    assert profile["last_updated"] == "2025-07-01"
    assert profile["open_weights"] is False

    # Limits
    assert profile["max_input_tokens"] == 200000
    assert profile["max_output_tokens"] == 64000

    # Capabilities
    assert profile["reasoning_output"] is True
    assert profile["tool_calling"] is True
    assert profile["tool_choice"] is True
    assert profile["structured_output"] is True
    assert profile["attachment"] is True

    # Modalities
    assert profile["text_inputs"] is True
    assert profile["image_inputs"] is True
    assert profile["pdf_inputs"] is True
    assert profile["text_outputs"] is True