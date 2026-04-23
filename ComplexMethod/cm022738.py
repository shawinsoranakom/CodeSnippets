async def test_garage_door_with_linked_obstruction_sensor(
    hass: HomeAssistant, hk_driver
) -> None:
    """Test if accessory and HA are updated accordingly with a linked obstruction sensor."""
    linked_obstruction_sensor_entity_id = "binary_sensor.obstruction"
    entity_id = "cover.garage_door"

    hass.states.async_set(linked_obstruction_sensor_entity_id, STATE_OFF)
    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = GarageDoorOpener(
        hass,
        hk_driver,
        "Garage Door",
        entity_id,
        2,
        {CONF_LINKED_OBSTRUCTION_SENSOR: linked_obstruction_sensor_entity_id},
    )
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 2
    assert acc.category == 4  # GarageDoorOpener

    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN

    hass.states.async_set(entity_id, CoverState.CLOSED)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_CLOSED
    assert acc.char_target_state.value == HK_DOOR_CLOSED
    assert acc.char_obstruction_detected.value is False

    hass.states.async_set(entity_id, CoverState.OPEN)
    hass.states.async_set(linked_obstruction_sensor_entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_OPEN
    assert acc.char_target_state.value == HK_DOOR_OPEN
    assert acc.char_obstruction_detected.value is True

    hass.states.async_set(entity_id, CoverState.CLOSED)
    hass.states.async_set(linked_obstruction_sensor_entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert acc.char_current_state.value == HK_DOOR_CLOSED
    assert acc.char_target_state.value == HK_DOOR_CLOSED
    assert acc.char_obstruction_detected.value is False

    hass.states.async_remove(entity_id)
    hass.states.async_remove(linked_obstruction_sensor_entity_id)
    await hass.async_block_till_done()