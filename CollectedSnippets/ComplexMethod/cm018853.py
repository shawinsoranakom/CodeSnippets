async def test_reconfigure(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    mock_api: MagicMock,
    new_email: str,
    expected_abort_reason: str,
    expected_placeholders: dict[str, str] | None,
    expected_access_token: str,
    expected_setup_calls: int,
) -> None:
    """Test the reconfiguration flow."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    assert result["url"] == (
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Prepare API responses
    mock_api.get_user = AsyncMock(return_value={"user": {"emailAddress": new_email}})
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_drive.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == expected_setup_calls

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == expected_abort_reason
    assert result.get("description_placeholders") == expected_placeholders

    assert config_entry.unique_id == TEST_USER_EMAIL
    assert "token" in config_entry.data

    # Verify access token is refreshed
    assert config_entry.data["token"].get("access_token") == expected_access_token
    assert config_entry.data["token"].get("refresh_token") == "mock-refresh-token"