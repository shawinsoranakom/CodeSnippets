async def test_indicator_test(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    indicator_test: Node,
    integration: MockConfigEntry,
) -> None:
    """Test that Indicators are discovered properly.

    This test covers indicators that we don't already have device fixtures for.
    """
    binary_sensor_entity_id = "binary_sensor.this_is_a_fake_device_binary_sensor"
    sensor_entity_id = "sensor.this_is_a_fake_device_sensor"
    switch_entity_id = "switch.this_is_a_fake_device_switch"

    for entity_id in (
        binary_sensor_entity_id,
        sensor_entity_id,
    ):
        entity_entry = entity_registry.async_get(entity_id)
        assert entity_entry
        assert entity_entry.entity_category == EntityCategory.DIAGNOSTIC
        assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert hass.states.get(entity_id) is None  # disabled by default
        entity_registry.async_update_entity(entity_id, disabled_by=None)

    entity_id = switch_entity_id
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.CONFIG
    assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(entity_id) is None  # disabled by default
    entity_registry.async_update_entity(entity_id, disabled_by=None)

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()
    client.async_send_command.reset_mock()

    entity_id = binary_sensor_entity_id
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    entity_id = sensor_entity_id
    state = hass.states.get(entity_id)
    assert state
    assert state.state == "0.0"

    entity_id = switch_entity_id
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == indicator_test.node_id
    assert args["valueId"] == {
        "commandClass": 135,
        "endpoint": 0,
        "property": "Test",
        "propertyKey": "Switch",
    }
    assert args["value"] is True

    client.async_send_command.reset_mock()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == indicator_test.node_id
    assert args["valueId"] == {
        "commandClass": 135,
        "endpoint": 0,
        "property": "Test",
        "propertyKey": "Switch",
    }
    assert args["value"] is False