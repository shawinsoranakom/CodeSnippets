async def test_binary_sensor_get_state(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    init_integration: MockConfigEntry,
    entity_id: str,
    uid: str,
    name: str,
    model: str,
) -> None:
    """Test states of the binary_sensor."""

    device = device_registry.async_get_device(identifiers={("freedompro", uid)})
    assert device is not None
    assert device.identifiers == {("freedompro", uid)}
    assert device.manufacturer == "Freedompro"
    assert device.name == name
    assert device.model == model

    state = hass.states.get(entity_id)
    assert state
    assert state.attributes.get("friendly_name") == name

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.unique_id == uid

    assert state.state == STATE_OFF

    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=[],
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes.get("friendly_name") == name

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == uid

        assert state.state == STATE_OFF

    states_response = get_states_response_for_uid(uid)
    if states_response[0]["type"] == "smokeSensor":
        states_response[0]["state"]["smokeDetected"] = True
    elif states_response[0]["type"] == "occupancySensor":
        states_response[0]["state"]["occupancyDetected"] = True
    elif states_response[0]["type"] == "motionSensor":
        states_response[0]["state"]["motionDetected"] = True
    elif states_response[0]["type"] == "contactSensor":
        states_response[0]["state"]["contactSensorState"] = True
    with patch(
        "homeassistant.components.freedompro.coordinator.get_states",
        return_value=states_response,
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=2))
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state
        assert state.attributes.get("friendly_name") == name

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.unique_id == uid

        assert state.state == STATE_ON