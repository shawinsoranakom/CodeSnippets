async def test_transportnsw_config(mocked_get_departures, hass: HomeAssistant) -> None:
    """Test minimal TransportNSW configuration."""
    assert await async_setup_component(hass, "sensor", VALID_CONFIG)
    await hass.async_block_till_done()
    state = hass.states.get("sensor.next_bus")
    assert state.state == "16"
    assert state.attributes["stop_id"] == "209516"
    assert state.attributes["route"] == "199"
    assert state.attributes["delay"] == 6
    assert state.attributes["real_time"] == "y"
    assert state.attributes["destination"] == "Palm Beach"
    assert state.attributes["mode"] == "Bus"
    assert state.attributes["device_class"] == SensorDeviceClass.DURATION
    assert state.attributes["state_class"] == SensorStateClass.MEASUREMENT