async def test_oauth_with_pkce_adds_code_verifier_to_token_resolve(
    hass: HomeAssistant,
    flow_handler: type[config_entry_oauth2_flow.AbstractOAuth2FlowHandler],
    local_impl_pkce: config_entry_oauth2_flow.LocalOAuth2ImplementationWithPkce,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Check pkce flow."""

    mock_integration(
        hass,
        MockModule(
            domain=TEST_DOMAIN,
            async_setup_entry=AsyncMock(return_value=True),
        ),
    )
    mock_platform(hass, f"{TEST_DOMAIN}.config_flow", None)
    flow_handler.async_register_implementation(hass, local_impl_pkce)

    result = await hass.config_entries.flow.async_init(
        TEST_DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    code_challenge = local_impl_pkce.compute_code_challenge(MOCK_SECRET_TOKEN_URLSAFE)
    assert result["type"] == data_entry_flow.FlowResultType.EXTERNAL_STEP

    assert result["url"].startswith(f"{AUTHORIZE_URL}?")
    assert f"client_id={CLIENT_ID}" in result["url"]
    assert "redirect_uri=https://example.com/auth/external/callback" in result["url"]
    assert f"state={state}" in result["url"]
    assert "scope=read+write" in result["url"]
    assert "response_type=code" in result["url"]
    assert f"code_challenge={code_challenge}" in result["url"]
    assert "code_challenge_method=S256" in result["url"]

    # Setup the response when HA tries to fetch a token with the code
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "refresh_token": REFRESH_TOKEN,
            "access_token": ACCESS_TOKEN_1,
            "type": "bearer",
            "expires_in": 60,
        },
    )

    client = await hass_client_no_auth()
    # trigger the callback
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    # Verify the token resolve request occurred
    assert len(aioclient_mock.mock_calls) == 1
    assert aioclient_mock.mock_calls[0][2] == {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": "abcd",
        "redirect_uri": "https://example.com/auth/external/callback",
        "code_verifier": MOCK_SECRET_TOKEN_URLSAFE,
    }