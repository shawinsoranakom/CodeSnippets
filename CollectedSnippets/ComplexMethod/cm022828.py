async def test_update(hass: HomeAssistant, fritz: Mock) -> None:
    """Test update without error."""
    device = FritzDeviceClimateMock()
    await setup_config_entry(
        hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 18
    assert state.attributes[ATTR_MAX_TEMP] == 28
    assert state.attributes[ATTR_MIN_TEMP] == 8
    assert state.attributes[ATTR_TEMPERATURE] == 19.5

    device.temperature = 19
    device.target_temperature = 20

    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(ENTITY_ID)

    assert fritz().update_devices.call_count == 2
    assert state
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 19
    assert state.attributes[ATTR_TEMPERATURE] == 20