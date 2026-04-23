async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
    fixture: str,
    abort_reason: str,
    placeholders: dict[str, str],
    call_count: int,
    access_token: str,
) -> None:
    """Test the re-authentication case updates the correct config entry.

    Make sure we abort if the user selects the
    wrong account on the consent screen.
    """
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
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with (
        patch(
            "homeassistant.components.google_mail.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "httplib2.Http.request",
            return_value=(
                Response({}),
                bytes(
                    await async_load_fixture(hass, f"{fixture}.json", DOMAIN),
                    encoding="UTF-8",
                ),
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result.get("type") is FlowResultType.ABORT
    assert result["reason"] == abort_reason
    assert result["description_placeholders"] == placeholders
    assert len(mock_setup.mock_calls) == call_count

    assert config_entry.unique_id == TITLE
    assert "token" in config_entry.data
    # Verify access token is refreshed
    assert config_entry.data["token"].get("access_token") == access_token
    assert config_entry.data["token"].get("refresh_token") == "mock-refresh-token"