async def test_infrared_send_command_success(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test sending IR command successfully."""
    await _mock_ir_device(mock_esphome_device, mock_client)

    command = NECCommand(address=0x04, command=0x08, modulation=38000)
    await infrared.async_send_command(hass, ENTITY_ID, command)

    # Verify the command was sent to the ESPHome client
    mock_client.infrared_rf_transmit_raw_timings.assert_called_once()
    call_args = mock_client.infrared_rf_transmit_raw_timings.call_args
    assert call_args[0][0] == 1  # key
    assert call_args[1]["carrier_frequency"] == 38000
    assert call_args[1]["device_id"] == 0

    # Verify timings (alternating positive/negative values)
    timings = call_args[1]["timings"]
    assert len(timings) > 0
    for i in range(0, len(timings), 2):
        assert timings[i] >= 0
    for i in range(1, len(timings), 2):
        assert timings[i] <= 0