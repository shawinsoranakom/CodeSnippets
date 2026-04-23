async def test_reauth_wrong_account(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    mock_automower_client: AsyncMock,
    jwt,
    user_id: str,
    reason: str,
    scope: str,
) -> None:
    """Test the reauthentication aborts, if user tries to reauthenticate with another account."""

    mock_config_entry.add_to_hass(hass)

    mock_config_entry.async_start_reauth(hass)
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
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": "mock-updated-token",
            "scope": "iam:read amc:api",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "provider": "husqvarna",
            "user_id": user_id,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    with patch(
        "homeassistant.components.husqvarna_automower.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == reason

    assert mock_config_entry.unique_id == USER_ID
    assert "token" in mock_config_entry.data
    # Verify access token is like before
    assert mock_config_entry.data["token"].get("access_token") == jwt
    assert (
        mock_config_entry.data["token"].get("refresh_token")
        == "3012bc9f-7a65-4240-b817-9154ffdcc30f"
    )