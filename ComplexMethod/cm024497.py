async def test_authentication_discovery_via_header(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_mcp_client: Mock,
    credential: None,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
    authenticate_header: str,
    resource_metadata_url: str,
    expected_scopes: list[str],
) -> None:
    """Test for an OAuth discovery flow using the WWW-Authenticate header."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # MCP Server returns 401 when first trying to connect via config flow validate_input. The response
    # value has a WWW-Authenticate header with a full URL for the resource metadata.
    mock_mcp_client.side_effect = httpx.HTTPStatusError(
        "Authentication required",
        request=None,
        response=httpx.Response(
            401,
            headers={
                "WWW-Authenticate": authenticate_header,
            },
        ),
    )

    # Discovery process starts. It hits the custom discovery URL directly.
    respx.get(resource_metadata_url).mock(
        return_value=OAUTH_PROTECTED_RESOURCE_METADATA_RESPONSE
    )
    respx.get(OAUTH_AUTHORIZATION_SERVER_DISCOVERY_ENDPOINT).mock(
        return_value=OAUTH_SERVER_METADATA_RESPONSE
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: MCP_SERVER_URL,
        },
    )

    # Should proceed to credentials choice
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
        authorize_url=OAUTH_AUTHORIZE_URL,
        token_url=OAUTH_TOKEN_URL,
        scopes=expected_scopes,
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
        CONF_AUTHORIZATION_URL: OAUTH_AUTHORIZE_URL,
        CONF_TOKEN_URL: OAUTH_TOKEN_URL,
        CONF_SCOPE: expected_scopes,
    }
    assert token
    token.pop("expires_at")
    assert token == OAUTH_TOKEN_PAYLOAD

    assert len(mock_setup_entry.mock_calls) == 1