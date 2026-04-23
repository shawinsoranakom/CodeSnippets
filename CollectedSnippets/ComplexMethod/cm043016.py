async def test_config_serialization_roundtrip():
    """memory_saving_mode and max_pages_before_recycle survive
    to_dict → from_kwargs → clone round-trips."""
    original = BrowserConfig(
        headless=True,
        memory_saving_mode=True,
        max_pages_before_recycle=500,
    )

    # to_dict → from_kwargs
    d = original.to_dict()
    assert d["memory_saving_mode"] is True
    assert d["max_pages_before_recycle"] == 500

    restored = BrowserConfig.from_kwargs(d)
    assert restored.memory_saving_mode is True
    assert restored.max_pages_before_recycle == 500

    # clone with override
    cloned = original.clone(max_pages_before_recycle=1000)
    assert cloned.memory_saving_mode is True  # inherited
    assert cloned.max_pages_before_recycle == 1000  # overridden

    # dump / load
    dumped = original.dump()
    loaded = BrowserConfig.load(dumped)
    assert loaded.memory_saving_mode is True
    assert loaded.max_pages_before_recycle == 500