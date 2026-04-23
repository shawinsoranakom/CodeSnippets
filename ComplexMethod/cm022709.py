async def test_fan_restore(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hk_driver
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "fan",
        "generic",
        "1234",
        suggested_object_id="simple",
    )
    entity_registry.async_get_or_create(
        "fan",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={"speed_list": ["off", "low", "medium", "high"]},
        supported_features=FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.DIRECTION,
        original_device_class="mock-device-class",
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    acc = Fan(hass, hk_driver, "Fan", "fan.simple", 2, None)
    assert acc.category == 3
    assert acc.char_active is not None
    assert acc.char_direction is None
    assert acc.char_speed is None
    assert acc.char_swing is None

    acc = Fan(hass, hk_driver, "Fan", "fan.all_info_set", 3, None)
    assert acc.category == 3
    assert acc.char_active is not None
    assert acc.char_direction is not None
    assert acc.char_speed is not None
    assert acc.char_swing is not None