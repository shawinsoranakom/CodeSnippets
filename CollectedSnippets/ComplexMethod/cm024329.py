async def test_lru_stats(hass: HomeAssistant, caplog: pytest.LogCaptureFixture) -> None:
    """Test logging lru stats."""

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    @lru_cache(maxsize=1)
    def _dummy_test_lru_stats():
        return 1

    class DomainData:
        def __init__(self) -> None:
            self._data = LRU(1)

    domain_data = DomainData()
    assert hass.services.has_service(DOMAIN, SERVICE_LRU_STATS)

    class LRUCache:
        def __init__(self) -> None:
            self._data = {"sqlalchemy_test": 1}

    sqlalchemy_lru_cache = LRUCache()

    def _mock_by_type(type_):
        if type_ == _LRU_CACHE_WRAPPER_OBJECT:
            return [_dummy_test_lru_stats]
        if type_ == _SQLALCHEMY_LRU_OBJECT:
            return [sqlalchemy_lru_cache]
        return [domain_data]

    with patch("objgraph.by_type", side_effect=_mock_by_type):
        await hass.services.async_call(DOMAIN, SERVICE_LRU_STATS, blocking=True)

    assert "DomainData" in caplog.text
    assert "(0, 0)" in caplog.text
    assert "_dummy_test_lru_stats" in caplog.text
    assert "CacheInfo" in caplog.text
    assert "sqlalchemy_test" in caplog.text