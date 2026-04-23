def test_usage_metadata_cache_creation_ttl() -> None:
    """Test _create_usage_metadata with granular cache_creation TTL fields."""

    # Case 1: cache_creation with specific ephemeral TTL tokens (BaseModel)
    class CacheCreation(BaseModel):
        ephemeral_5m_input_tokens: int = 100
        ephemeral_1h_input_tokens: int = 50

    class UsageWithCacheCreation(BaseModel):
        input_tokens: int = 200
        output_tokens: int = 30
        cache_read_input_tokens: int = 10
        cache_creation_input_tokens: int = 150
        cache_creation: CacheCreation = CacheCreation()

    result = _create_usage_metadata(UsageWithCacheCreation())
    # input_tokens = 200 (base) + 10 (cache_read) + 150 (specific: 100+50)
    assert result["input_tokens"] == 360
    assert result["output_tokens"] == 30
    assert result["total_tokens"] == 390
    details = dict(result.get("input_token_details") or {})
    assert details["cache_read"] == 10
    # cache_creation should be suppressed to avoid double counting
    assert details["cache_creation"] == 0
    assert details["ephemeral_5m_input_tokens"] == 100
    assert details["ephemeral_1h_input_tokens"] == 50

    # Case 2: cache_creation as a dict
    class UsageWithCacheCreationDict(BaseModel):
        input_tokens: int = 200
        output_tokens: int = 30
        cache_read_input_tokens: int = 10
        cache_creation_input_tokens: int = 150
        cache_creation: dict = {
            "ephemeral_5m_input_tokens": 80,
            "ephemeral_1h_input_tokens": 70,
        }

    result = _create_usage_metadata(UsageWithCacheCreationDict())
    assert result["input_tokens"] == 200 + 10 + 80 + 70
    details = dict(result.get("input_token_details") or {})
    assert details["cache_creation"] == 0
    assert details["ephemeral_5m_input_tokens"] == 80
    assert details["ephemeral_1h_input_tokens"] == 70

    # Case 3: cache_creation exists but specific keys are zero — falls back to
    # generic cache_creation_input_tokens
    class CacheCreationZero(BaseModel):
        ephemeral_5m_input_tokens: int = 0
        ephemeral_1h_input_tokens: int = 0

    class UsageWithCacheCreationZero(BaseModel):
        input_tokens: int = 200
        output_tokens: int = 30
        cache_read_input_tokens: int = 10
        cache_creation_input_tokens: int = 50
        cache_creation: CacheCreationZero = CacheCreationZero()

    result = _create_usage_metadata(UsageWithCacheCreationZero())
    # specific_cache_creation_tokens = 0, so falls back to cache_creation_input_tokens
    # input_tokens = 200 + 10 + 50 = 260
    assert result["input_tokens"] == 260
    assert result["output_tokens"] == 30
    assert result["total_tokens"] == 290
    details = dict(result.get("input_token_details") or {})
    assert details["cache_read"] == 10
    assert details["cache_creation"] == 50

    # Case 4: cache_creation exists but specific keys are missing from the dict
    class CacheCreationEmpty(BaseModel):
        pass

    class UsageWithCacheCreationEmpty(BaseModel):
        input_tokens: int = 100
        output_tokens: int = 20
        cache_read_input_tokens: int = 5
        cache_creation_input_tokens: int = 15
        cache_creation: CacheCreationEmpty = CacheCreationEmpty()

    result = _create_usage_metadata(UsageWithCacheCreationEmpty())
    # specific_cache_creation_tokens = 0, falls back to cache_creation_input_tokens
    assert result["input_tokens"] == 100 + 5 + 15
    assert result["output_tokens"] == 20
    assert result["total_tokens"] == 140
    details = dict(result.get("input_token_details") or {})
    assert details["cache_creation"] == 15

    # Case 5: only one ephemeral key is non-zero
    class CacheCreationPartial(BaseModel):
        ephemeral_5m_input_tokens: int = 0
        ephemeral_1h_input_tokens: int = 75

    class UsageWithPartialCache(BaseModel):
        input_tokens: int = 100
        output_tokens: int = 10
        cache_read_input_tokens: int = 0
        cache_creation_input_tokens: int = 75
        cache_creation: CacheCreationPartial = CacheCreationPartial()

    result = _create_usage_metadata(UsageWithPartialCache())
    # specific_cache_creation_tokens = 75 > 0, so generic cache_creation is suppressed
    assert result["input_tokens"] == 100 + 0 + 75
    assert result["output_tokens"] == 10
    assert result["total_tokens"] == 185
    details = dict(result.get("input_token_details") or {})
    assert details["cache_creation"] == 0
    assert details["ephemeral_1h_input_tokens"] == 75
    # ephemeral_5m_input_tokens is 0 — still included since 0 is not None
    assert details["ephemeral_5m_input_tokens"] == 0

    # Case 6: no cache_creation field at all (the pre-existing path)
    class UsageNoCacheCreation(BaseModel):
        input_tokens: int = 50
        output_tokens: int = 25
        cache_read_input_tokens: int = 5
        cache_creation_input_tokens: int = 10

    result = _create_usage_metadata(UsageNoCacheCreation())
    assert result["input_tokens"] == 50 + 5 + 10
    assert result["output_tokens"] == 25
    assert result["total_tokens"] == 90
    details = dict(result.get("input_token_details") or {})
    assert details["cache_read"] == 5
    assert details["cache_creation"] == 10