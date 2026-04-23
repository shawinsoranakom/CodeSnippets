def test_usage_metadata_standardization() -> None:
    class UsageModel(BaseModel):
        input_tokens: int = 10
        output_tokens: int = 5
        cache_read_input_tokens: int = 3
        cache_creation_input_tokens: int = 2

    # Happy path
    usage = UsageModel()
    result = _create_usage_metadata(usage)
    assert result["input_tokens"] == 15  # 10 + 3 + 2
    assert result["output_tokens"] == 5
    assert result["total_tokens"] == 20
    assert result.get("input_token_details") == {"cache_read": 3, "cache_creation": 2}

    # Null input and output tokens
    class UsageModelNulls(BaseModel):
        input_tokens: int | None = None
        output_tokens: int | None = None
        cache_read_input_tokens: int | None = None
        cache_creation_input_tokens: int | None = None

    usage_nulls = UsageModelNulls()
    result = _create_usage_metadata(usage_nulls)
    assert result["input_tokens"] == 0
    assert result["output_tokens"] == 0
    assert result["total_tokens"] == 0

    # Test missing fields
    class UsageModelMissing(BaseModel):
        pass

    usage_missing = UsageModelMissing()
    result = _create_usage_metadata(usage_missing)
    assert result["input_tokens"] == 0
    assert result["output_tokens"] == 0
    assert result["total_tokens"] == 0