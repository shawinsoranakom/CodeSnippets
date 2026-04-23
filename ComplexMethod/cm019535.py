async def test_cover_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hub_ping: AsyncMock,
    mock_hub_configuration: AsyncMock,
    mock_hub_status: AsyncMock,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the device is created correctly."""
    mock_hub_configuration = request.getfixturevalue(mock_hub_configuration)
    mock_hub_status = request.getfixturevalue(mock_hub_status)

    assert await setup_config_entry(hass, mock_config_entry)
    assert len(mock_hub_ping.mock_calls) == 1
    assert len(mock_hub_configuration.mock_calls) == 1
    assert len(mock_hub_status.mock_calls) > 0

    device_entries = device_registry.devices.get_devices_for_config_entry_id(
        mock_config_entry.entry_id
    )
    assert len(device_entries) > 1

    device_entries = list(
        filter(
            lambda e: e.identifiers != {(DOMAIN, mock_config_entry.entry_id)},
            device_entries,
        )
    )
    assert len(device_entries) > 0
    for device_entry in device_entries:
        assert device_entry == snapshot(name=f"device-{device_entry.serial_number}")