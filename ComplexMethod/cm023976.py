async def test_reauth_flow(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    profile: None,
    setup_credentials: None,
) -> None:
    """Test OAuth reauthentication flow will update existing config entry."""
    config_entry.add_to_hass(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    # config_entry.req initiates reauth
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}"
        "&scope=activity+heartrate+nutrition+profile+settings+sleep+weight&prompt=none"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": "60",
        },
    )

    with patch(
        "homeassistant.components.fitbit.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1

    assert config_entry.data["token"]["refresh_token"] == "updated-refresh-token"