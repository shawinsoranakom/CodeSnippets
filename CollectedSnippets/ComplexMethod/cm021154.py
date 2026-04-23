async def test_transportnsw_config_not_found(
    mocked_get_departures_not_found, hass: HomeAssistant
) -> None:
    """Test minimal TransportNSW configuration."""
    assert await async_setup_component(hass, "sensor", VALID_CONFIG)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.next_bus")
    assert state.state == "unknown"
    assert state.attributes["stop_id"] == "209516"
    assert state.attributes["route"] is None
    assert state.attributes["delay"] is None
    assert state.attributes["real_time"] is None
    assert state.attributes["destination"] is None
    assert state.attributes["mode"] is None