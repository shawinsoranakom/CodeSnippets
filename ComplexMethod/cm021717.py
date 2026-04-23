async def test_dynamic_attributes(
    hass: HomeAssistant, device: MagicMock, config_entry: MagicMock
) -> None:
    """Test dynamic attributes."""
    await init_integration(hass, config_entry)

    entity_id = f"climate.{device.name}"
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.OFF
    attributes = state.attributes
    assert attributes["current_temperature"] == 20
    assert attributes["current_humidity"] == 50

    device.system_mode = "cool"
    device.current_temperature = 21
    device.current_humidity = 55

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.COOL
    attributes = state.attributes
    assert attributes["current_temperature"] == 21
    assert attributes["current_humidity"] == 55

    device.system_mode = "heat"
    device.current_temperature = 61
    device.current_humidity = 50

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.HEAT
    attributes = state.attributes
    assert attributes["current_temperature"] == 61
    assert attributes["current_humidity"] == 50

    device.system_mode = "auto"

    async_fire_time_changed(
        hass,
        utcnow() + SCAN_INTERVAL,
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == HVACMode.HEAT_COOL
    attributes = state.attributes
    assert attributes["current_temperature"] == 61
    assert attributes["current_humidity"] == 50