def test_create_usage_metadata_with_cached_and_reasoning_tokens() -> None:
    """Test usage metadata with both cached and reasoning tokens."""
    token_usage = {
        "prompt_tokens": 2006,
        "completion_tokens": 450,
        "total_tokens": 2456,
        "input_tokens_details": {"cached_tokens": 1920},
        "output_tokens_details": {"reasoning_tokens": 200},
    }

    result = _create_usage_metadata(token_usage)

    assert isinstance(result, dict)
    assert result["input_tokens"] == 2006
    assert result["output_tokens"] == 450
    assert result["total_tokens"] == 2456

    assert "input_token_details" in result
    assert isinstance(result["input_token_details"], dict)
    assert result["input_token_details"]["cache_read"] == 1920

    assert "output_token_details" in result
    assert isinstance(result["output_token_details"], dict)
    assert result["output_token_details"]["reasoning"] == 200