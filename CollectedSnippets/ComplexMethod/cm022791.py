async def test_unexpected_exceptions(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    microbees: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test unknown error from server."""
    await setup_integration(hass, config_entry)
    microbees.return_value.getMyProfile.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"
    aioclient_mock.clear_requests()
    aioclient_mock.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == error