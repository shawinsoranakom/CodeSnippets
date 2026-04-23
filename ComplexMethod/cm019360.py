async def test_web_reauth_flow(
    hass: HomeAssistant,
    mock_code_flow: Mock,
    mock_exchange: Mock,
    aioclient_mock: AiohttpClientMocker,
    hass_client_no_auth: ClientSessionGenerator,
    entry_data: dict[str, Any],
) -> None:
    """Test reauth of an existing config entry with a web credential."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **entry_data,
            "auth_implementation": DOMAIN,
            "token": {"access_token": "OLD_ACCESS_TOKEN"},
        },
    )
    config_entry.add_to_hass(hass)
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.google.api.OAuth2WebServerFlow.step1_get_device_and_user_codes",
        side_effect=OAuth2DeviceCodeError(
            "Invalid response 401. Error: invalid_client"
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"],
            user_input={},
        )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result.get("type") is FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=https://www.googleapis.com/auth/calendar"
        "&access_type=offline&prompt=consent"
    )

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
            "scope": "https://www.googleapis.com/auth/calendar",
        },
    )

    with patch(
        "homeassistant.components.google.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    data = dict(entries[0].data)
    data["token"].pop("expires_at")
    data["token"].pop("expires_in")
    assert data == {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": "mock-access-token",
            "refresh_token": "mock-refresh-token",
            "scope": "https://www.googleapis.com/auth/calendar",
            "token_type": "Bearer",
        },
        "credential_type": "web_auth",
    }

    assert len(mock_setup.mock_calls) == 1