def test_create_usage_metadata_with_cached_tokens() -> None:
    """Test usage metadata with prompt caching."""
    token_usage = {
        "prompt_tokens": 2006,
        "completion_tokens": 300,
        "total_tokens": 2306,
        "input_tokens_details": {"cached_tokens": 1920},
    }

    result = _create_usage_metadata(token_usage)

    assert isinstance(result, dict)
    assert result["input_tokens"] == 2006
    assert result["output_tokens"] == 300
    assert result["total_tokens"] == 2306
    assert "input_token_details" in result
    assert isinstance(result["input_token_details"], dict)
    assert result["input_token_details"]["cache_read"] == 1920
    assert "output_token_details" not in result