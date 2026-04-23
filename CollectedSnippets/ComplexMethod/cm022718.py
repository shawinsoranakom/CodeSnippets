async def test_filter_life_level_linked_sensors(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test that a linked filter life level sensor exposed."""
    entity_id = "fan.demo"
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
        },
    )

    filter_life_level_entity_id = "sensor.demo_filter_life_level"
    hass.states.async_set(filter_life_level_entity_id, 50)

    await hass.async_block_till_done()
    acc = AirPurifier(
        hass,
        hk_driver,
        "Air Purifier",
        entity_id,
        1,
        {
            CONF_LINKED_FILTER_LIFE_LEVEL: filter_life_level_entity_id,
        },
    )
    hk_driver.add_accessory(acc)

    assert acc.linked_filter_change_indicator_binary_sensor is None
    assert (
        acc.char_filter_change_indication is not None
    )  # calculated based on filter life level
    assert acc.linked_filter_life_level_sensor is not None
    assert acc.char_filter_life_level is not None

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_filter_change_indication.value == FILTER_OK
    assert acc.char_filter_life_level.value == 50

    hass.states.async_set(
        filter_life_level_entity_id, THRESHOLD_FILTER_CHANGE_NEEDED - 1
    )
    await hass.async_block_till_done()
    assert acc.char_filter_life_level.value == THRESHOLD_FILTER_CHANGE_NEEDED - 1
    assert acc.char_filter_change_indication.value == FILTER_CHANGE_FILTER