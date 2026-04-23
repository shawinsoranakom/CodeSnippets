async def test_reauthentication(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test yolink reauthentication."""
    await setup.async_setup_component(
        hass,
        DOMAIN,
        {},
    )

    await application_credentials.async_import_client_credential(
        hass,
        DOMAIN,
        application_credentials.ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )

    old_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        version=1,
        data={
            "refresh_token": "outdated_fresh_token",
            "access_token": "outdated_access_token",
        },
    )
    old_entry.add_to_hass(hass)

    result = await old_entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    result = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with (
        patch("homeassistant.components.yolink.api.ConfigEntryAuth"),
        patch(
            "homeassistant.components.yolink.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
    token_data = old_entry.data["token"]
    assert token_data["access_token"] == "mock-access-token"
    assert token_data["refresh_token"] == "mock-refresh-token"
    assert token_data["type"] == "Bearer"
    assert token_data["expires_in"] == 60
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(mock_setup.mock_calls) == 1