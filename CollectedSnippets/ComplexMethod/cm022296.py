async def test_reconfigure_flow_success(
    hass: HomeAssistant,
    mock_duco_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test a successful reconfigure flow updates host and reloads."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_duco_client.async_get_board_info.side_effect = DucoConnectionError(
        "Connection refused"
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.50"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_duco_client.async_get_board_info.side_effect = None
    new_host = "192.168.1.200"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: new_host}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == new_host