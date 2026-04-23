async def test_setup_entry(
    hass: HomeAssistant,
    device_registry: DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    mock_mozart_client: AsyncMock,
) -> None:
    """Test async_setup_entry."""

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED

    # Load entry
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Check that the device has been registered properly
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, TEST_SERIAL_NUMBER)}
    )
    assert device is not None
    # Is usually TEST_NAME, but is updated to the device's friendly name by _update_name_and_beolink
    assert device.name == TEST_FRIENDLY_NAME
    assert device.model == TEST_MODEL_BALANCE

    # Ensure that the connection has been checked WebSocket connection has been initialized
    assert mock_mozart_client.check_device_connection.call_count == 1
    assert mock_mozart_client.close_api_client.call_count == 0
    assert mock_mozart_client.connect_notifications.call_count == 1