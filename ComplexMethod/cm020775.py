async def test_fan_set_off(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    init_integration: MockConfigEntry,
) -> None:
    """Test turn off the fan."""

    entity_id = "fan.bedroom"

    states_response = get_states_response_for_uid(uid)
    states_response[0]["state"]["on"] = True
    states_response[0]["state"]["rotationSpeed"] = 50
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        await async_update_entity(hass, entity_id)
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_PERCENTAGE] == 50
    assert state.attributes.get("friendly_name") == "bedroom"

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    with patch("homeassistant.components.freedompro.fan.put_state") as mock_put_state:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
    mock_put_state.assert_called_once_with(ANY, ANY, ANY, '{"on": false}')

    states_response[0]["state"]["on"] = False
    states_response[0]["state"]["rotationSpeed"] = 0
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        await async_update_entity(hass, entity_id)
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_PERCENTAGE] == 0
    assert state.state == STATE_OFF