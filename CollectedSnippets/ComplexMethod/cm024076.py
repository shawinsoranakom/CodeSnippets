async def test_reconfiguration_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    access_token: str,
    unique_id: str,
    expected_result: str,
    expires_at: float,
) -> None:
    """Test reconfigure step with correct params."""

    CURRENT_TOKEN = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": access_token,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires_at,
        },
    }
    assert hass.config_entries.async_update_entry(
        mock_config_entry,
        data=CURRENT_TOKEN,
    )
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["step_id"] == "auth"

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    assert result["url"] == (
        f"{AUTHORIZATION_ENDPOINT}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}&scope=restapi+offline_access+openid"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"{REDIRECT_PATH}?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        TOKEN_ENDPOINT,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": "60",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == expected_result

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1