async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test initialization of the reauth flow."""
    assert await setup.async_setup_component(hass, "neato", {})
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    entry = MockConfigEntry(
        entry_id="my_entry",
        domain=DOMAIN,
        data={"username": "abcdef", "password": "123456", "vendor": "neato"},
    )
    entry.add_to_hass(hass)

    # Should show form
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Confirm reauth flow
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})

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

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    # Update entry
    with patch(
        "homeassistant.components.neato.async_setup_entry", return_value=True
    ) as mock_setup:
        result3 = await hass.config_entries.flow.async_configure(result2["flow_id"])
        await hass.async_block_till_done()

    new_entry = hass.config_entries.async_get_entry("my_entry")

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert new_entry.state is ConfigEntryState.LOADED
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1