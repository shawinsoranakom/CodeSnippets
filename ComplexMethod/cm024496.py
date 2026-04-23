async def test_authentication_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_mcp_client: Mock,
    credential: None,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
    oauth_server_metadata_response: httpx.Response,
    expected_authorize_url: str,
    expected_token_url: str,
    scopes: list[str] | None,
) -> None:
    """Test for an OAuth authentication flow for an MCP server."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # MCP Server returns 401 indicating the client needs to authenticate
    mock_mcp_client.side_effect = httpx.HTTPStatusError(
        "Authentication required", request=None, response=httpx.Response(401)
    )
    # Prepare the OAuth Server metadata
    respx.get(OAUTH_DISCOVERY_ENDPOINT).mock(
        return_value=oauth_server_metadata_response
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: MCP_SERVER_URL,
        },
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "credentials_choice"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "next_step_id": "pick_implementation",
        },
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    result = await perform_oauth_flow(
        hass,
        aioclient_mock,
        hass_client_no_auth,
        result,
        authorize_url=expected_authorize_url,
        token_url=expected_token_url,
        scopes=scopes,
    )

    # Client now accepts credentials
    mock_mcp_client.side_effect = None
    response = Mock()
    response.serverInfo.name = TEST_API_NAME
    mock_mcp_client.return_value.initialize.return_value = response

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_API_NAME
    data = result["data"]
    token = data.pop(CONF_TOKEN)
    assert data == {
        "auth_implementation": AUTH_DOMAIN,
        CONF_URL: MCP_SERVER_URL,
        CONF_AUTHORIZATION_URL: expected_authorize_url,
        CONF_TOKEN_URL: expected_token_url,
        CONF_SCOPE: scopes,
    }
    assert token
    token.pop("expires_at")
    assert token == OAUTH_TOKEN_PAYLOAD

    assert len(mock_setup_entry.mock_calls) == 1