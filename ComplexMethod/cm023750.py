async def test_window_shuttler(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    cube: MaxCube,
    windowshutter: MaxWindowShutter,
) -> None:
    """Test a successful setup with a shuttler device."""
    assert entity_registry.async_is_registered(ENTITY_ID)
    entity = entity_registry.async_get(ENTITY_ID)
    assert entity.unique_id == "AABBCCDD03"
    assert entity.entity_category == EntityCategory.DIAGNOSTIC

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_FRIENDLY_NAME) == "TestRoom TestShutter"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.WINDOW

    windowshutter.is_open = False
    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF