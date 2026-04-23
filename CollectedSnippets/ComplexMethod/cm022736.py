async def test_windowcovering_basic_restore(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, hk_driver
) -> None:
    """Test setting up an entity from state in the event registry."""
    hass.set_state(CoreState.not_running)

    entity_registry.async_get_or_create(
        "cover",
        "generic",
        "1234",
        suggested_object_id="simple",
    )
    entity_registry.async_get_or_create(
        "cover",
        "generic",
        "9012",
        suggested_object_id="all_info_set",
        capabilities={},
        supported_features=CoverEntityFeature.STOP,
        original_device_class="mock-device-class",
    )

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START, {})
    await hass.async_block_till_done()

    acc = WindowCoveringBasic(hass, hk_driver, "Cover", "cover.simple", 2, None)
    assert acc.category == 14
    assert acc.char_current_position is not None
    assert acc.char_target_position is not None
    assert acc.char_position_state is not None

    acc = WindowCoveringBasic(hass, hk_driver, "Cover", "cover.all_info_set", 3, None)
    assert acc.category == 14
    assert acc.char_current_position is not None
    assert acc.char_target_position is not None
    assert acc.char_position_state is not None