def test_create_usage_metadata_with_reasoning_tokens() -> None:
    """Test usage metadata with reasoning tokens."""
    token_usage = {
        "prompt_tokens": 100,
        "completion_tokens": 450,
        "total_tokens": 550,
        "output_tokens_details": {"reasoning_tokens": 200},
    }

    result = _create_usage_metadata(token_usage)

    assert isinstance(result, dict)
    assert result["input_tokens"] == 100
    assert result["output_tokens"] == 450
    assert result["total_tokens"] == 550
    assert "output_token_details" in result
    assert isinstance(result["output_token_details"], dict)
    assert result["output_token_details"]["reasoning"] == 200
    assert "input_token_details" not in result