async def test_config_parameter_switch(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    hank_binary_switch,
    integration,
    client,
) -> None:
    """Test config parameter switch is created."""
    switch_entity_id = "switch.smart_plug_with_two_usb_ports_overload_protection"
    entity_entry = entity_registry.async_get(switch_entity_id)
    assert entity_entry
    assert entity_entry.disabled

    updated_entry = entity_registry.async_update_entity(
        switch_entity_id, disabled_by=None
    )
    assert updated_entry != entity_entry
    assert updated_entry.disabled is False
    assert entity_entry.entity_category == EntityCategory.CONFIG

    # reload integration and check if entity is correctly there
    await hass.config_entries.async_reload(integration.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(switch_entity_id)
    assert state
    assert state.state == STATE_ON

    client.async_send_command.reset_mock()

    # Test turning on
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {"entity_id": switch_entity_id}, blocking=True
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == hank_binary_switch.node_id
    assert args["value"] == 1
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 20,
    }

    client.async_send_command.reset_mock()

    # Test turning off
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {"entity_id": switch_entity_id}, blocking=True
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == hank_binary_switch.node_id
    assert args["value"] == 0
    assert args["valueId"] == {
        "commandClass": 112,
        "endpoint": 0,
        "property": 20,
    }

    client.async_send_command.reset_mock()
    client.async_send_command.side_effect = FailedZWaveCommand("test", 1, "test")

    # Test turning off error raises proper exception
    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {"entity_id": switch_entity_id},
            blocking=True,
        )

    assert str(err.value) == (
        "Unable to set value 32-112-0-20: zwave_error: Z-Wave error 1 - test"
    )