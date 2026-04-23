async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_dropbox_client,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test creating a new config entry through the OAuth flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    result_url = URL(result["url"])
    assert f"{result_url.origin()}{result_url.path}" == OAUTH2_AUTHORIZE
    assert result_url.query["response_type"] == "code"
    assert result_url.query["client_id"] == CLIENT_ID
    assert (
        result_url.query["redirect_uri"] == "https://example.com/auth/external/callback"
    )
    assert result_url.query["state"] == state
    assert result_url.query["scope"] == " ".join(OAUTH2_SCOPES)
    assert result_url.query["token_access_type"] == "offline"
    assert result_url.query["code_challenge"]
    assert result_url.query["code_challenge_method"] == "S256"

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ACCOUNT_EMAIL
    assert result["data"]["token"]["access_token"] == "mock-access-token"
    assert result["result"].unique_id == ACCOUNT_ID
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1