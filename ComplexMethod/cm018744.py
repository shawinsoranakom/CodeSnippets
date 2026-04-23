async def test_import_migration(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test if importing step with migration works."""
    old_entry = MockConfigEntry(domain=DOMAIN, unique_id="123", version=1)
    old_entry.add_to_hass(hass)

    await setup_component(hass)

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].version == 1

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    flow = hass.config_entries.flow._progress[flows[0]["flow_id"]]
    assert flow.migrate_entry == old_entry.entry_id

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": flows[0]["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"], {"implementation": "eneco"}
    )

    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")
    aioclient_mock.post(
        "https://api.toon.eu/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("toonapi.Toon.agreements", return_value=[Agreement(agreement_id=123)]):
        result = await hass.config_entries.flow.async_configure(flows[0]["flow_id"])

    assert result["type"] is FlowResultType.CREATE_ENTRY

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].version == 2