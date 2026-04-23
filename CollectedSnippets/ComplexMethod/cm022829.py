async def test_preset_mode_update(hass: HomeAssistant, fritz: Mock) -> None:
    """Test preset mode."""
    device = FritzDeviceClimateMock()
    device.comfort_temperature = 23
    device.eco_temperature = 20
    await setup_config_entry(
        hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.attributes[ATTR_PRESET_MODE] is None

    # test comfort preset
    device.target_temperature = 23
    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(ENTITY_ID)

    assert fritz().update_devices.call_count == 2
    assert state
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_COMFORT

    # test eco preset
    device.target_temperature = 20
    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(ENTITY_ID)

    assert fritz().update_devices.call_count == 3
    assert state
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_ECO

    # test boost preset by special temp
    device.target_temperature = 127  # special temp from the api
    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(ENTITY_ID)

    assert fritz().update_devices.call_count == 4
    assert state
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_BOOST

    # test boost preset by boost_active
    device.target_temperature = 21
    device.boost_active = True
    next_update = dt_util.utcnow() + timedelta(seconds=200)
    async_fire_time_changed(hass, next_update)
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(ENTITY_ID)

    assert fritz().update_devices.call_count == 5
    assert state
    assert state.attributes[ATTR_PRESET_MODE] == PRESET_BOOST