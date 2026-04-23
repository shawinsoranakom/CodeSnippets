def test_memory_config() -> None:
    default_config = RedisMemoryConfig()
    assert default_config.redis_url == "redis://localhost:6379"
    assert default_config.index_name == "chat_history"
    assert default_config.prefix == "memory"
    assert default_config.distance_metric == "cosine"
    assert default_config.algorithm == "flat"
    assert default_config.top_k == 10
    assert default_config.distance_threshold == 0.7
    assert default_config.model_name == "sentence-transformers/all-mpnet-base-v2"
    assert not default_config.sequential

    # test we can specify each of these values
    url = "rediss://localhost:7010"
    name = "custom name"
    prefix = "custom prefix"
    metric = "ip"
    algorithm = "hnsw"
    k = 5
    distance = 0.25
    model = "redis/langcache-embed-v1"

    custom_config = RedisMemoryConfig(
        redis_url=url,
        index_name=name,
        prefix=prefix,
        distance_metric=metric,  # type: ignore[arg-type]
        algorithm=algorithm,  # type: ignore[arg-type]
        top_k=k,
        distance_threshold=distance,
        model_name=model,
    )
    assert custom_config.redis_url == url
    assert custom_config.index_name == name
    assert custom_config.prefix == prefix
    assert custom_config.distance_metric == metric
    assert custom_config.algorithm == algorithm
    assert custom_config.top_k == k
    assert custom_config.distance_threshold == distance
    assert custom_config.model_name == model

    # test that Literal values are validated correctly
    with pytest.raises(ValidationError):
        _ = RedisMemoryConfig(distance_metric="approximate")  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        _ = RedisMemoryConfig(algorithm="pythagoras")