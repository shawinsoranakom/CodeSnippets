async def test_reauth_flow_success(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    tibber_mock: MagicMock,
) -> None:
    """Test successful reauthentication flow."""
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            AUTH_IMPLEMENTATION: DOMAIN,
            CONF_TOKEN: {"access_token": "old-token"},
        },
        unique_id="unique_user_id",
        title="Existing",
    )
    existing_entry.add_to_hass(hass)

    result = await existing_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    _mock_tibber(tibber_mock)
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    authorize_url = result["url"]
    state = parse_qs(urlparse(authorize_url).query)["state"][0]

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK

    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "expires_in": 3600,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert existing_entry.data[CONF_TOKEN]["access_token"] == "new-access-token"