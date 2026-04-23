def test_override_single_value() -> None:
    """Test values with exact match."""
    store = EV({ent: {"key": "value"}})
    store.get.cache_clear()
    assert store.get(ent) == {"key": "value"}
    assert store.get.cache_info().currsize == 1
    assert store.get.cache_info().misses == 1
    assert store.get(ent) == {"key": "value"}
    assert store.get.cache_info().currsize == 1
    assert store.get.cache_info().misses == 1
    assert store.get.cache_info().hits == 1