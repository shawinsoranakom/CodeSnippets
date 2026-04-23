async def test_duration_characteristic_properties(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test SetDuration and RemainingDuration characteristic properties from linked entity attributes."""
    entity_id = "switch.sprinkler"
    linked_duration_entity = "input_number.valve_duration"
    linked_end_time_entity = "sensor.valve_end_time"

    # Case 1: linked input_number has min, max, step attributes
    hass.states.async_set(entity_id, STATE_OFF)
    hass.states.async_set(
        linked_duration_entity,
        "120",
        {
            "min": 10,
            "max": 900,
            "step": 5,
        },
    )
    hass.states.async_set(linked_end_time_entity, dt_util.utcnow().isoformat())
    await hass.async_block_till_done()

    acc = ValveSwitch(
        hass,
        hk_driver,
        "Sprinkler",
        entity_id,
        5,
        {
            "type": "sprinkler",
            "linked_valve_duration": linked_duration_entity,
            "linked_valve_end_time": linked_end_time_entity,
        },
    )
    acc.run()
    await hass.async_block_till_done()

    set_duration_props = acc.char_set_duration.properties
    assert set_duration_props["minValue"] == 10
    assert set_duration_props["maxValue"] == 900
    assert set_duration_props["minStep"] == 5

    remaining_duration_props = acc.char_remaining_duration.properties
    assert remaining_duration_props["minValue"] == 0
    assert remaining_duration_props["maxValue"] == 900
    assert remaining_duration_props["minStep"] == 1

    # Case 2: linked input_number missing attributes, should use defaults
    hass.states.async_set(
        linked_duration_entity,
        "60",
        {},  # No min, max, step
    )
    await hass.async_block_till_done()

    acc = ValveSwitch(
        hass,
        hk_driver,
        "Sprinkler",
        entity_id,
        6,
        {
            "type": "sprinkler",
            "linked_valve_duration": linked_duration_entity,
            "linked_valve_end_time": linked_end_time_entity,
        },
    )
    acc.run()
    await hass.async_block_till_done()

    set_duration_props = acc.char_set_duration.properties
    assert set_duration_props["minValue"] == 0
    assert set_duration_props["maxValue"] == 3600
    assert set_duration_props["minStep"] == 1

    remaining_duration_props = acc.char_remaining_duration.properties
    assert remaining_duration_props["minValue"] == 0
    assert remaining_duration_props["maxValue"] == 60 * 60 * 48
    assert remaining_duration_props["minStep"] == 1

    # Case 4: linked input_number missing attribute value, should use defaults
    hass.states.async_set(
        linked_duration_entity,
        "60",
        {
            "min": 900,
            "max": None,  # No value
        },
    )
    await hass.async_block_till_done()

    acc = ValveSwitch(
        hass,
        hk_driver,
        "Sprinkler",
        entity_id,
        6,
        {
            "type": "sprinkler",
            "linked_valve_duration": linked_duration_entity,
            "linked_valve_end_time": linked_end_time_entity,
        },
    )
    acc.run()
    await hass.async_block_till_done()

    set_duration_props = acc.char_set_duration.properties
    assert set_duration_props["minValue"] == 900
    assert set_duration_props["maxValue"] == 3600
    assert set_duration_props["minStep"] == 1

    remaining_duration_props = acc.char_remaining_duration.properties
    assert remaining_duration_props["minValue"] == 0
    assert remaining_duration_props["maxValue"] == 60 * 60 * 48
    assert remaining_duration_props["minStep"] == 1

    # Case 3: linked input_number missing state, should use defaults
    hass.states.async_remove(linked_duration_entity)
    await hass.async_block_till_done()

    acc = ValveSwitch(
        hass,
        hk_driver,
        "Sprinkler",
        entity_id,
        7,
        {
            "type": "sprinkler",
            "linked_valve_duration": linked_duration_entity,
            "linked_valve_end_time": linked_end_time_entity,
        },
    )
    acc.run()
    await hass.async_block_till_done()

    set_duration_props = acc.char_set_duration.properties
    assert set_duration_props["minValue"] == 0
    assert set_duration_props["maxValue"] == 3600
    assert set_duration_props["minStep"] == 1

    remaining_duration_props = acc.char_remaining_duration.properties
    assert remaining_duration_props["minValue"] == 0
    assert remaining_duration_props["maxValue"] == 60 * 60 * 48
    assert remaining_duration_props["minStep"] == 1

    # Case 5: Attribute is not valid
    assert acc._get_linked_duration_property("invalid_property", 1000) == 1000