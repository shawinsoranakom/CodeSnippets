async def test_data_api_diagnostics_with_devices(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    data_api_client_mock: MagicMock,
    setup_credentials: None,
) -> None:
    """Test Data API diagnostics with successful device retrieval."""
    devices = {
        "device-1": create_tibber_device(
            device_id="device-1",
            name="Device 1",
            brand="Tibber",
            model="Test Model",
        ),
        "device-2": create_tibber_device(
            device_id="device-2",
            name="Device 2",
            brand="Tibber",
            model="Test Model",
        ),
    }

    data_api_client_mock.get_all_devices = AsyncMock(return_value=devices)
    data_api_client_mock.update_devices = AsyncMock(return_value=devices)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, config_entry)

    assert isinstance(result, dict)
    assert "homes" in result
    assert "devices" in result

    devices_list = result["devices"]
    assert isinstance(devices_list, list)
    assert len(devices_list) == 2

    device_1 = next((d for d in devices_list if d["id"] == "device-1"), None)
    assert device_1 is not None
    assert device_1["name"] == "Device 1"
    assert device_1["brand"] == "Tibber"
    assert device_1["model"] == "Test Model"

    device_2 = next((d for d in devices_list if d["id"] == "device-2"), None)
    assert device_2 is not None
    assert device_2["name"] == "Device 2"
    assert device_2["brand"] == "Tibber"
    assert device_2["model"] == "Test Model"