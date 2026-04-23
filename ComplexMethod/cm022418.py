async def test_remove_config_entry_from_device_if_integration_remove(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test removing config entry from device doesn't lead to an error when the integration removes the entry."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    can_remove = False

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        if can_remove:
            device_registry.async_update_device(
                device_entry.id, remove_config_entry_id=config_entry.entry_id
            )
        return can_remove

    mock_integration(
        hass,
        MockModule(
            "comp1", async_remove_config_entry_device=async_remove_config_entry_device
        ),
    )
    mock_integration(
        hass,
        MockModule(
            "comp2", async_remove_config_entry_device=async_remove_config_entry_device
        ),
    )

    entry_1 = MockConfigEntry(
        domain="comp1",
        title="Test 1",
        source="bla",
    )
    entry_1.supports_remove_device = True
    entry_1.add_to_hass(hass)

    entry_2 = MockConfigEntry(
        domain="comp1",
        title="Test 1",
        source="bla",
    )
    entry_2.supports_remove_device = True
    entry_2.add_to_hass(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert device_entry.config_entries == {entry_1.entry_id, entry_2.entry_id}

    # Try removing a config entry from the device, it should fail because
    # async_remove_config_entry_device returns False
    response = await ws_client.remove_device(device_entry.id, entry_1.entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"

    # Make async_remove_config_entry_device return True
    can_remove = True

    # Remove the 1st config entry
    response = await ws_client.remove_device(device_entry.id, entry_1.entry_id)

    assert response["success"]
    assert response["result"]["config_entries"] == [entry_2.entry_id]

    # Check that the config entry was removed from the device
    assert device_registry.async_get(device_entry.id).config_entries == {
        entry_2.entry_id
    }

    # Remove the 2nd config entry
    response = await ws_client.remove_device(device_entry.id, entry_2.entry_id)

    assert response["success"]
    assert response["result"] is None

    # This was the last config entry, the device is removed
    assert not device_registry.async_get(device_entry.id)