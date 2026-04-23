async def test_config_reauth_profile(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    polling_config_entry: MockConfigEntry,
    monzo: AsyncMock,
) -> None:
    """Test reauth an existing profile reauthenticates the config entry."""
    await setup_integration(hass, polling_config_entry)

    result = await polling_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
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
        f"{OAUTH2_AUTHORIZE}/?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
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
            "access_token": "new-mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
            "user_id": str(USER_ID),
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "await_approval_confirmation"
    assert polling_config_entry.data["token"]["access_token"] == "mock-access-token"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"confirm": True}
    )

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert result
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert polling_config_entry.data["token"]["access_token"] == "new-mock-access-token"