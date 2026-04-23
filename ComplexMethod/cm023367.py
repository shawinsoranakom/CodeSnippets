async def test_reconfigure_flow_success(
    hass: HomeAssistant, mock_hass_splunk: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """Test successful reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_TOKEN: "new-token-456",
            CONF_HOST: "new-splunk.example.com",
            CONF_PORT: 9088,
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
            CONF_NAME: "Updated Splunk",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "new-splunk.example.com"
    assert mock_config_entry.data[CONF_PORT] == 9088
    assert mock_config_entry.data[CONF_TOKEN] == "new-token-456"
    assert mock_config_entry.data[CONF_SSL] is True
    assert mock_config_entry.data[CONF_VERIFY_SSL] is False
    assert mock_config_entry.data[CONF_NAME] == "Updated Splunk"
    assert mock_config_entry.title == "new-splunk.example.com:9088"