async def test_get_action_capabilities_set_tilt_pos(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_cover_entities: list[MockCover],
) -> None:
    """Test we get the expected capabilities from a cover action."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[3]
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "position",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    assert len(actions) == 5
    action_types = {action["type"] for action in actions}
    assert action_types == {
        "open",
        "close",
        "set_tilt_position",
        "open_tilt",
        "close_tilt",
    }
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        if action["type"] == "set_tilt_position":
            assert capabilities == expected_capabilities
        else:
            assert capabilities == {"extra_fields": []}