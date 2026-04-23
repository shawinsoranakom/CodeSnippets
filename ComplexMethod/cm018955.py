async def test_reauth_multiple_servers_available(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    mock_plex_calls: None,
    requests_mock: requests_mock.Mocker,
    plextv_resources_two_servers: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test setup and reauthorization of a Plex token when multiple servers are available."""
    requests_mock.get(
        "https://plex.tv/api/v2/resources",
        text=plextv_resources_two_servers,
    )

    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    flow_id = result["flow_id"]

    with (
        patch("plexauth.PlexAuth.initiate_auth"),
        patch("plexauth.PlexAuth.token", return_value="BRAND_NEW_TOKEN"),
    ):
        result = await hass.config_entries.flow.async_configure(flow_id, user_input={})
        assert result["type"] is FlowResultType.EXTERNAL_STEP

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.EXTERNAL_STEP_DONE

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.ABORT
        assert result["flow_id"] == flow_id
        assert result["reason"] == "reauth_successful"

    assert len(hass.config_entries.flow.async_progress()) == 0
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert entry.state is ConfigEntryState.LOADED
    assert entry.data[CONF_SERVER] == "Plex Server 1"
    assert entry.data[CONF_SERVER_IDENTIFIER] == "unique_id_123"
    assert entry.data[PLEX_SERVER_CONFIG][CONF_URL] == PLEX_DIRECT_URL
    assert entry.data[PLEX_SERVER_CONFIG][CONF_TOKEN] == "BRAND_NEW_TOKEN"

    mock_setup_entry.assert_called_once()