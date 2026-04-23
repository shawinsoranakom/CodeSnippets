async def test_zooz_zen72(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    switch_zooz_zen72: Node,
    integration: MockConfigEntry,
) -> None:
    """Test that Zooz ZEN72 Indicators are discovered as number entities."""
    entity_id = "number.z_wave_plus_700_series_dimmer_switch_indicator_value"
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
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_VALUE: 5,
        },
        blocking=True,
    )
    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == switch_zooz_zen72.node_id
    assert args["valueId"] == {
        "commandClass": 135,
        "endpoint": 0,
        "property": "value",
    }
    assert args["value"] == 5

    client.async_send_command.reset_mock()

    entity_id = "button.z_wave_plus_700_series_dimmer_switch_identify"
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category == EntityCategory.CONFIG
    assert entity_entry.disabled_by is None
    assert hass.states.get(entity_id) is not None
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == switch_zooz_zen72.node_id
    assert args["valueId"] == {
        "commandClass": 135,
        "endpoint": 0,
        "property": "identify",
    }
    assert args["value"] is True