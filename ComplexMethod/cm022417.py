async def test_remove_config_entry_from_device_fails(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test removing config entry from device failing cases."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    async def async_remove_config_entry_device(
        hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
    ) -> bool:
        return True

    mock_integration(
        hass,
        MockModule("comp1"),
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
    entry_1.add_to_hass(hass)

    entry_2 = MockConfigEntry(
        domain="comp2",
        title="Test 1",
        source="bla",
    )
    entry_2.supports_remove_device = True
    entry_2.add_to_hass(hass)

    entry_3 = MockConfigEntry(
        domain="comp3",
        title="Test 1",
        source="bla",
    )
    entry_3.supports_remove_device = True
    entry_3.add_to_hass(hass)

    device_registry.async_get_or_create(
        config_entry_id=entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_registry.async_get_or_create(
        config_entry_id=entry_2.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry_3.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    assert device_entry.config_entries == {
        entry_1.entry_id,
        entry_2.entry_id,
        entry_3.entry_id,
    }

    fake_entry_id = "abc123"
    assert entry_1.entry_id != fake_entry_id
    fake_device_id = "abc123"
    assert device_entry.id != fake_device_id

    # Try removing a non existing config entry from the device
    response = await ws_client.remove_device(device_entry.id, fake_entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert response["error"]["message"] == "Unknown config entry"

    # Try removing a config entry which does not support removal from the device
    response = await ws_client.remove_device(device_entry.id, entry_1.entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert (
        response["error"]["message"] == "Config entry does not support device removal"
    )

    # Try removing a config entry from a device which does not exist
    response = await ws_client.remove_device(fake_device_id, entry_2.entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert response["error"]["message"] == "Unknown device"

    # Try removing a config entry from a device which it's not connected to
    response = await ws_client.remove_device(device_entry.id, entry_2.entry_id)

    assert response["success"]
    assert set(response["result"]["config_entries"]) == {
        entry_1.entry_id,
        entry_3.entry_id,
    }

    response = await ws_client.remove_device(device_entry.id, entry_2.entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert response["error"]["message"] == "Config entry not in device"

    # Try removing a config entry which can't be loaded from a device - allowed
    response = await ws_client.remove_device(device_entry.id, entry_3.entry_id)

    assert not response["success"]
    assert response["error"]["code"] == "home_assistant_error"
    assert response["error"]["message"] == "Integration not found"