async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_madvr_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # define new host
    new_host = "192.168.1.100"
    # make sure setting port works
    new_port = 44078

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: new_host, CONF_PORT: new_port},
    )

    # should get the abort with success result
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify that the config entry was updated
    assert mock_config_entry.data[CONF_HOST] == new_host
    assert mock_config_entry.data[CONF_PORT] == new_port

    # Verify that the connection was tested
    mock_madvr_client.open_connection.assert_called()
    mock_madvr_client.async_add_tasks.assert_called()
    mock_madvr_client.async_cancel_tasks.assert_called()