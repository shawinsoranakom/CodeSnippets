async def test_filter_maintenance_linked_sensors(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test that a linked filter level and filter change indicator are exposed."""
    entity_id = "fan.demo"
    hass.states.async_set(
        entity_id,
        STATE_ON,
        {
            ATTR_SUPPORTED_FEATURES: FanEntityFeature.SET_SPEED,
        },
    )

    filter_change_indicator_entity_id = "binary_sensor.demo_filter_change_indicator"
    hass.states.async_set(filter_change_indicator_entity_id, STATE_OFF)

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
            CONF_LINKED_FILTER_CHANGE_INDICATION: filter_change_indicator_entity_id,
            CONF_LINKED_FILTER_LIFE_LEVEL: filter_life_level_entity_id,
        },
    )
    hk_driver.add_accessory(acc)

    assert acc.linked_filter_change_indicator_binary_sensor is not None
    assert acc.char_filter_change_indication is not None
    assert acc.linked_filter_life_level_sensor is not None
    assert acc.char_filter_life_level is not None

    acc.run()
    await hass.async_block_till_done()

    assert acc.char_filter_change_indication.value == FILTER_OK
    assert acc.char_filter_life_level.value == 50

    # Updated filter change indicator should reflect in HomeKit
    broker = MagicMock()
    acc.char_filter_change_indication.broker = broker
    hass.states.async_set(filter_change_indicator_entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert acc.char_filter_change_indication.value == FILTER_CHANGE_FILTER
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    # Change to same state should not trigger update in HomeKit
    hass.states.async_set(
        filter_change_indicator_entity_id, STATE_ON, force_update=True
    )
    await hass.async_block_till_done()
    assert acc.char_filter_change_indication.value == FILTER_CHANGE_FILTER
    assert len(broker.mock_calls) == 0

    # Updated filter life level should reflect in HomeKit
    broker = MagicMock()
    acc.char_filter_life_level.broker = broker
    hass.states.async_set(filter_life_level_entity_id, 25)
    await hass.async_block_till_done()
    assert acc.char_filter_life_level.value == 25
    assert len(broker.mock_calls) == 2
    broker.reset_mock()

    # Change to same state should not trigger update in HomeKit
    hass.states.async_set(filter_life_level_entity_id, 25, force_update=True)
    await hass.async_block_till_done()
    assert acc.char_filter_life_level.value == 25
    assert len(broker.mock_calls) == 0

    # Should handle unavailable state, show last known value
    hass.states.async_set(filter_change_indicator_entity_id, STATE_UNAVAILABLE)
    hass.states.async_set(filter_life_level_entity_id, STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert acc.char_filter_change_indication.value == FILTER_CHANGE_FILTER
    assert acc.char_filter_life_level.value == 25

    # Check that all goes well if we remove the linked sensors
    hass.states.async_remove(filter_change_indicator_entity_id)
    hass.states.async_remove(filter_life_level_entity_id)
    await hass.async_block_till_done()
    acc.run()
    await hass.async_block_till_done()
    assert len(acc.char_filter_change_indication.broker.mock_calls) == 0
    assert len(acc.char_filter_life_level.broker.mock_calls) == 0

    # HomeKit will show the last known values
    assert acc.char_filter_change_indication.value == FILTER_CHANGE_FILTER
    assert acc.char_filter_life_level.value == 25