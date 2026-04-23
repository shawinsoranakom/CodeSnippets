async def test_single_available_server(
    hass: HomeAssistant,
    mock_plex_calls,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test creating an entry with one server available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

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

    mock_setup_entry.assert_called_once()