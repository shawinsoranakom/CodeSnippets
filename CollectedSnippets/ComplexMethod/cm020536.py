async def test_full_flow_reconfigure_exceptions(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    mock_setup_entry: MagicMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    reason: str,
) -> None:
    """Test the full flow of the config flow, this time with exceptions."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_portainer_client.portainer_system_status.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": reason}

    mock_portainer_client.portainer_system_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_API_TOKEN] == "new_api_key"
    assert mock_config_entry.data[CONF_URL] == "https://new_domain:9000/"
    assert mock_config_entry.data[CONF_VERIFY_SSL] is True
    assert len(mock_setup_entry.mock_calls) == 1