async def test_adding_last_unconfigured_server(
    hass: HomeAssistant,
    mock_plex_calls,
    requests_mock: requests_mock.Mocker,
    plextv_resources_two_servers,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test automatically adding last unconfigured server when multiple servers on account."""
    MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SERVER_IDENTIFIER: MOCK_SERVERS[1][CONF_SERVER_IDENTIFIER],
            CONF_SERVER: MOCK_SERVERS[1][CONF_SERVER],
        },
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    requests_mock.get(
        "https://plex.tv/api/v2/resources",
        text=plextv_resources_two_servers,
    )

    with (
        patch("plexauth.PlexAuth.initiate_auth"),
        patch("plexauth.PlexAuth.token", return_value=MOCK_TOKEN),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] is FlowResultType.EXTERNAL_STEP

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.EXTERNAL_STEP_DONE

        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.CREATE_ENTRY

        assert (
            result["title"] == "https://1-2-3-4.123456789001234567890.plex.direct:32400"
        )
        assert result["data"][CONF_SERVER] == "Plex Server 1"
        assert result["data"][CONF_SERVER_IDENTIFIER] == "unique_id_123"
        assert (
            result["data"][PLEX_SERVER_CONFIG][CONF_URL]
            == "https://1-2-3-4.123456789001234567890.plex.direct:32400"
        )
        assert result["data"][PLEX_SERVER_CONFIG][CONF_TOKEN] == MOCK_TOKEN

    assert mock_setup_entry.call_count == 2