async def test_window_shuttler_battery(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    cube: MaxCube,
    windowshutter: MaxWindowShutter,
) -> None:
    """Test battery binary_state with a shuttler device."""
    assert entity_registry.async_is_registered(BATTERY_ENTITY_ID)
    entity = entity_registry.async_get(BATTERY_ENTITY_ID)
    assert entity.unique_id == "AABBCCDD03_battery"
    assert entity.entity_category == EntityCategory.DIAGNOSTIC

    state = hass.states.get(BATTERY_ENTITY_ID)
    assert state is not None
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.BATTERY
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "TestRoom TestShutter battery"

    windowshutter.battery = 1  # maxcube-api MAX_DEVICE_BATTERY_LOW
    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(BATTERY_ENTITY_ID)
    assert state.state == STATE_ON  # on means low

    windowshutter.battery = 0  # maxcube-api MAX_DEVICE_BATTERY_OK
    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)
    state = hass.states.get(BATTERY_ENTITY_ID)
    assert state.state == STATE_OFF