async def test_migration_wrong_location(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_smartthings: AsyncMock,
    mock_old_config_entry: MockConfigEntry,
) -> None:
    """Test SmartThings reauthentication with wrong location."""
    mock_old_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_old_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_old_config_entry.state is ConfigEntryState.SETUP_ERROR

    mock_smartthings.get_locations.return_value[
        0
    ].location_id = "123123123-2be1-4e40-b257-e4ef59083324"

    result = hass.config_entries.flow.async_progress()[0]

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

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
        "https://auth-global.api.smartthings.com/oauth/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 82806,
            "scope": "r:devices:* w:devices:* x:devices:* r:hubs:* "
            "r:locations:* w:locations:* x:locations:* "
            "r:scenes:* x:scenes:* r:rules:* w:rules:* sse",
            "access_tier": 0,
            "installed_app_id": "123123123-2be1-4e40-b257-e4ef59083324",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_location_mismatch"
    assert mock_old_config_entry.state is ConfigEntryState.SETUP_ERROR
    assert mock_old_config_entry.data == {
        OLD_DATA: {CONF_LOCATION_ID: "397678e5-9995-4a39-9d9f-ae6ba310236c"}
    }
    assert (
        mock_old_config_entry.unique_id
        == "appid123-2be1-4e40-b257-e4ef59083324_397678e5-9995-4a39-9d9f-ae6ba310236c"
    )
    assert mock_old_config_entry.version == 3
    assert mock_old_config_entry.minor_version == 3
    mock_smartthings.get_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    mock_smartthings.delete_installed_app.assert_called_once_with(
        "mock-access-token",
        "123aa123-2be1-4e40-b257-e4ef59083324",
    )
    mock_smartthings.delete_smart_app.assert_called_once_with(
        "mock-access-token",
        "c6cde2b0-203e-44cf-a510-3b3ed4706996",
    )