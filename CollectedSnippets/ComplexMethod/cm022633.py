async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    setup_credentials,
    setup_userinfo,
    user_identifier: str,
    abort_reason: str,
    resulting_access_token: str,
    starting_unique_id: str | None,
) -> None:
    """Test the re-authentication case updates the correct config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=starting_unique_id,
        data={
            "token": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access",
            }
        },
    )
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
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
        "&scope=https://www.googleapis.com/auth/tasks+"
        "https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_tasks.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result["type"] == "abort"
    assert result["reason"] == abort_reason

    assert config_entry.unique_id == "123"
    assert "token" in config_entry.data
    # Verify access token is refreshed
    assert config_entry.data["token"]["access_token"] == resulting_access_token
    assert config_entry.data["token"]["refresh_token"] == "mock-refresh-token"