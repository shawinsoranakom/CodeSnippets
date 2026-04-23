async def test_remove_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test we can remove devices that are not available."""
    assert await async_setup_component(hass, "config", {})

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id) is True

    inject_bluetooth_service_info(hass, MOCK_SERVICE_INFO)

    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, MOCK_SERVICE_INFO.address)}
    )
    assert device_entry

    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, config_entry.entry_id)
    assert not response["success"]

    await hass.async_block_till_done()
    assert device_registry.async_get(device_entry.id)

    with patch_discovered_devices([]):
        response = await client.remove_device(device_entry.id, config_entry.entry_id)
        assert response["success"]

        await hass.async_block_till_done()
        assert not device_registry.async_get(device_entry.id)