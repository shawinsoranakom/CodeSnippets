async def test_cached_event_message(hass: HomeAssistant) -> None:
    """Test that we cache event messages."""

    events = []

    @callback
    def _event_listener(event):
        events.append(event)

    hass.bus.async_listen(EVENT_STATE_CHANGED, _event_listener)

    hass.states.async_set("light.window", "on")
    hass.states.async_set("light.window", "off")
    await hass.async_block_till_done()

    assert len(events) == 2
    lru_event_cache.cache_clear()

    msg0 = cached_event_message(b"2", events[0])
    assert msg0 == cached_event_message(b"2", events[0])

    msg1 = cached_event_message(b"2", events[1])
    assert msg1 == cached_event_message(b"2", events[1])

    assert msg0 != msg1

    cache_info = lru_event_cache.cache_info()
    assert cache_info.hits == 2
    assert cache_info.misses == 2
    assert cache_info.currsize == 2

    cached_event_message(b"2", events[1])
    cache_info = lru_event_cache.cache_info()
    assert cache_info.hits == 3
    assert cache_info.misses == 2
    assert cache_info.currsize == 2