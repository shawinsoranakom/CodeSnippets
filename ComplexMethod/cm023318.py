async def test_thermostat_fan(
    hass: HomeAssistant,
    client,
    climate_adc_t3000,
    integration,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the fan entity for a z-wave fan."""
    node = climate_adc_t3000
    entity_id = "fan.adc_t3000"

    state = hass.states.get(entity_id)
    assert state is None

    entry = entity_registry.async_get(entity_id)
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Test enabling entity
    updated_entry = entity_registry.async_update_entity(entity_id, disabled_by=None)
    assert updated_entry != entry
    assert updated_entry.disabled is False

    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    client.async_send_command.reset_mock()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_FAN_STATE) == "Idle / off"
    assert state.attributes.get(ATTR_PRESET_MODE) == "Auto low"
    assert (
        state.attributes.get(ATTR_SUPPORTED_FEATURES)
        == FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    # Test setting preset mode
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "Low"},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 68
    assert args["valueId"] == {
        "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
        "endpoint": 0,
        "property": "mode",
    }
    assert args["value"] == 1

    client.async_send_command.reset_mock()

    # Test setting unknown preset mode
    with pytest.raises(NotValidPresetModeError) as exc:
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "Turbo"},
            blocking=True,
        )
    assert exc.value.translation_key == "not_valid_preset_mode"

    client.async_send_command.reset_mock()

    # Test turning off
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 68
    assert args["valueId"] == {
        "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
        "endpoint": 0,
        "property": "off",
    }
    assert args["value"]

    client.async_send_command.reset_mock()

    # Test turning on
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 68
    assert args["valueId"] == {
        "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
        "endpoint": 0,
        "property": "off",
    }
    assert not args["value"]

    client.async_send_command.reset_mock()

    # Test fan state update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Thermostat Fan State",
                "commandClass": CommandClass.THERMOSTAT_FAN_STATE.value,
                "endpoint": 0,
                "property": "state",
                "newValue": 4,
                "prevValue": 0,
                "propertyName": "state",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state.attributes.get(ATTR_FAN_STATE) == "Circulation mode"

    client.async_send_command.reset_mock()

    # Test unknown fan state update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Thermostat Fan State",
                "commandClass": CommandClass.THERMOSTAT_FAN_STATE.value,
                "endpoint": 0,
                "property": "state",
                "newValue": 99,
                "prevValue": 0,
                "propertyName": "state",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert not state.attributes.get(ATTR_FAN_STATE)

    client.async_send_command.reset_mock()

    # Test fan mode update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Thermostat Fan Mode",
                "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
                "endpoint": 0,
                "property": "mode",
                "newValue": 1,
                "prevValue": 0,
                "propertyName": "mode",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state.attributes.get(ATTR_PRESET_MODE) == "Low"

    client.async_send_command.reset_mock()

    # Test fan mode update from value updated event for an unknown mode
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Thermostat Fan Mode",
                "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
                "endpoint": 0,
                "property": "mode",
                "newValue": 79,
                "prevValue": 0,
                "propertyName": "mode",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert not state.attributes.get(ATTR_PRESET_MODE)

    client.async_send_command.reset_mock()

    # Test fan mode turned off update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 68,
            "args": {
                "commandClassName": "Thermostat Fan Mode",
                "commandClass": CommandClass.THERMOSTAT_FAN_MODE.value,
                "endpoint": 0,
                "property": "off",
                "newValue": True,
                "prevValue": False,
                "propertyName": "off",
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF