async def test_reauth_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_mcp_client: Mock,
    credential: None,
    config_entry_with_auth: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Test for an OAuth authentication flow for an MCP server."""
    config_entry_with_auth.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    result = await perform_oauth_flow(
        hass, aioclient_mock, hass_client_no_auth, result, scopes=SCOPES
    )

    # Verify we can connect to the server
    response = Mock()
    response.serverInfo.name = TEST_API_NAME
    mock_mcp_client.return_value.initialize.return_value = response

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert config_entry_with_auth.unique_id == AUTH_DOMAIN
    assert config_entry_with_auth.title == TEST_API_NAME
    data = {**config_entry_with_auth.data}
    token = data.pop(CONF_TOKEN)
    assert data == {
        "auth_implementation": AUTH_DOMAIN,
        CONF_URL: MCP_SERVER_URL,
        CONF_AUTHORIZATION_URL: OAUTH_AUTHORIZE_URL,
        CONF_TOKEN_URL: OAUTH_TOKEN_URL,
        CONF_SCOPE: ["read", "write"],
    }
    assert token
    token.pop("expires_at")
    assert token == OAUTH_TOKEN_PAYLOAD

    assert len(mock_setup_entry.mock_calls) == 1