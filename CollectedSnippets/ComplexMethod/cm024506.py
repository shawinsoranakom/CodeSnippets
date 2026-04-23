async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    jwt: str,
    mock_setup_entry: Mock,
) -> None:
    """Check full flow."""
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

    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt,
            "scope": "any",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": "mock-user-id",
            "expires_at": 1697753347,
        },
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == USER_ID

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["result"].unique_id == USER_ID
    assert entry.data == {
        "auth_implementation": "yale",
        "token": {
            "access_token": jwt,
            "expires_at": ANY,
            "expires_in": ANY,
            "refresh_token": "mock-refresh-token",
            "scope": "any",
            "user_id": "mock-user-id",
        },
    }