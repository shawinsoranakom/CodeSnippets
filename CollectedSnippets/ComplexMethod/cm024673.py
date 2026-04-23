async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    user_identifier: str,
    abort_reason: str,
    resulting_access_token: str,
    mock_setup: Mock,
    expected_setup_calls: int,
) -> None:
    """Test the re-authentication case updates the correct config entry."""

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
        "&scope=https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        "+https://www.googleapis.com/auth/photoslibrary.appendonly"
        "+https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == abort_reason

    assert config_entry.unique_id == USER_IDENTIFIER
    assert config_entry.title == "Account Name"
    config_entry_data = dict(config_entry.data)
    assert "token" in config_entry_data
    assert "expires_at" in config_entry_data["token"]
    del config_entry_data["token"]["expires_at"]
    assert config_entry_data == {
        "auth_implementation": DOMAIN,
        "token": {
            # Verify token is refreshed or not
            "access_token": resulting_access_token,
            "expires_in": EXPIRES_IN,
            "refresh_token": FAKE_REFRESH_TOKEN,
            "type": "Bearer",
            "scope": (
                "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
                " https://www.googleapis.com/auth/photoslibrary.appendonly"
                " https://www.googleapis.com/auth/userinfo.profile"
            ),
        },
    }
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == expected_setup_calls