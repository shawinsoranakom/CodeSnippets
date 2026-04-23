async def test_full_flow_reconfigure_unique_id_mismatch(
    hass: HomeAssistant,
    mock_portainer_client: AsyncMock,
    mock_setup_entry: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure aborts when credentials point to a different Portainer instance."""
    mock_config_entry.add_to_hass(hass)
    mock_portainer_client.portainer_system_status.return_value = PortainerSystemStatus(
        instance_id="different-instance-id", version="2.0.0"
    )
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT_RECONFIGURE,
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert mock_config_entry.data[CONF_API_TOKEN] == "test_api_token"
    assert mock_config_entry.data[CONF_URL] == "https://127.0.0.1:9000/"
    assert len(mock_setup_entry.mock_calls) == 0