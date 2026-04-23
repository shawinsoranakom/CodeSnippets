async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reconfiguration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "10.0.0.1",
            CONF_API_TOKEN: "new-api-token",
            CONF_VERIFY_SSL: True,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_HOST] == "10.0.0.1"
    assert mock_config_entry.data[CONF_API_TOKEN] == "new-api-token"
    assert mock_config_entry.data[CONF_VERIFY_SSL] is True