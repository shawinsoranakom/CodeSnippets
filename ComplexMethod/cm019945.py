async def test_get_action_capabilities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    # Test with entity without optional capabilities
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
    ).entity_id
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    assert len(actions) == 3
    action_types = {action["type"] for action in actions}
    assert action_types == {"turn_on", "toggle", "turn_off"}
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        assert capabilities == {"extra_fields": []}

    # Test without entity
    entity_registry.async_remove(entity_id)
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        assert capabilities in ({"extra_fields": []}, {})