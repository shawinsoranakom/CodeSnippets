async def test_reconfigure_flow_cannot_connect(
    hass: HomeAssistant,
    mock_hdfury_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguration fails with cannot connect."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {}

    # Simulate a connection error by raising a HDFuryError
    mock_hdfury_client.get_board.side_effect = HDFuryError()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.124",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert result["data_schema"]({}) == {CONF_HOST: "192.168.1.123"}

    # Attempt with valid IP should work
    mock_hdfury_client.get_board.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.124",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Changed entry
    assert mock_config_entry.data[CONF_HOST] == "192.168.1.124"
    assert mock_config_entry.unique_id == "000123456789"