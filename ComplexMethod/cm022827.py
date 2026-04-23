async def test_remove_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    hass_ws_client: WebSocketGenerator,
    fritz: Mock,
) -> None:
    """Test removing of a device."""
    assert await async_setup_component(hass, "config", {})
    assert await setup_config_entry(
        hass,
        MOCK_CONFIG[DOMAIN][CONF_DEVICES][0],
        f"{DOMAIN}.{CONF_FAKE_NAME}",
        FritzDeviceSwitchMock(),
        fritz,
    )
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries()
    assert len(entries) == 1

    entry = entries[0]
    assert entry.supports_remove_device

    entity = entity_registry.async_get("switch.fake_name")
    good_device = device_registry.async_get(entity.device_id)

    orphan_device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "0000 000000")},
    )

    # try to delete good_device
    ws_client = await hass_ws_client(hass)
    response = await ws_client.remove_device(good_device.id, entry.entry_id)
    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    await hass.async_block_till_done()

    # try to delete orphan_device
    ws_client = await hass_ws_client(hass)
    response = await ws_client.remove_device(orphan_device.id, entry.entry_id)
    assert response["success"]
    await hass.async_block_till_done()