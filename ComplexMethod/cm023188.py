async def test_notification_idle_button(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    multisensor_6: Node,
    integration: MockConfigEntry,
) -> None:
    """Test Notification idle button."""
    node = multisensor_6
    entity_id = "button.multisensor_6_idle_home_security_cover_status"
    entity_entry = entity_registry.async_get(entity_id)
    assert entity_entry
    assert entity_entry.entity_category is EntityCategory.CONFIG
    assert entity_entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert hass.states.get(entity_id) is None  # disabled by default

    entity_registry.async_update_entity(
        entity_id,
        disabled_by=None,
    )
    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == "unknown"
    assert (
        state.attributes["friendly_name"]
        == "Multisensor 6 Idle Home Security Cover status"
    )

    # Test successful idle call
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )

    assert client.async_send_command_no_wait.call_count == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "node.manually_idle_notification_value"
    assert args["nodeId"] == node.node_id
    assert args["valueId"] == {
        "commandClass": 113,
        "endpoint": 0,
        "property": "Home Security",
        "propertyKey": "Cover status",
    }