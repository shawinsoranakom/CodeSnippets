async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    reauth_jwt: str,
    mock_setup_entry: Mock,
) -> None:
    """Test the reauthentication case updates the existing config entry."""

    mock_config_entry.add_to_hass(hass)

    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "auth"

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": reauth_jwt,
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": USER_ID,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert mock_config_entry.unique_id == USER_ID
    assert "token" in mock_config_entry.data
    # Verify access token is refreshed
    assert mock_config_entry.data["token"]["access_token"] == reauth_jwt