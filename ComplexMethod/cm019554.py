async def test_remove_config_entry_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    matter_client: MagicMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that a device can be removed ok."""
    assert await async_setup_component(hass, "config", {})
    await setup_integration_with_node_fixture(hass, "device_diagnostics", matter_client)
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    device_entry = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )[0]
    entity_id = "light.m5stamp_lighting_app"

    assert device_entry
    assert entity_registry.async_get(entity_id)
    assert hass.states.get(entity_id)

    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    assert response["success"]
    await hass.async_block_till_done()

    assert not device_registry.async_get(device_entry.id)
    assert not entity_registry.async_get(entity_id)
    assert not hass.states.get(entity_id)