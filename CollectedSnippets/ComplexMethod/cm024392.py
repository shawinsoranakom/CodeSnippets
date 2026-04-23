async def test_reconfigure_flow_abort_incorrect_device(
    hass: HomeAssistant,
    mock_hdfury_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test ip of other device with different serial."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # Simulate different serial number, as if user entered wrong IP
    mock_hdfury_client.get_board.return_value = {
        "hostname": "VRROOM-21",
        "ipaddress": "192.168.1.124",
        "serial": "000987654321",
        "pcbv": "3",
        "version": "FW: 0.61",
    }
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.124",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "incorrect_device"

    # Entry should still be original entry
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.123"
    assert mock_config_entry.unique_id == "000123456789"