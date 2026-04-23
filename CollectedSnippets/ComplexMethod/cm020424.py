async def test_reauth_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that the reauth flow works."""

    await setup_integration(hass, mock_config_entry)

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await _do_get_token(hass, result, hass_client_no_auth, aioclient_mock)
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN] == "mock-access-token"
    assert mock_config_entry.data[CONF_TOKEN]["refresh_token"] == "mock-refresh-token"
    assert mock_config_entry.data[CONF_FOLDER_PATH] == "backups/home_assistant"
    assert mock_config_entry.data[CONF_FOLDER_ID] == "my_folder_id"
    assert mock_config_entry.data[CONF_TENANT_ID] == TENANT_ID