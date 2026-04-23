async def test_manual_config_with_token(
    hass: HomeAssistant,
    mock_plex_calls,
    requests_mock: requests_mock.Mocker,
    empty_library,
    empty_payload,
) -> None:
    """Test creating via manual configuration with only token."""

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_advanced"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"setup_method": MANUAL_SETUP_STRING}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"

    with (
        patch("homeassistant.components.plex.GDM", return_value=MockGDM(disabled=True)),
        patch("homeassistant.components.plex.PlexWebsocket", autospec=True),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_TOKEN: MOCK_TOKEN}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    mock_url = "https://1-2-3-4.123456789001234567890.plex.direct:32400"

    assert result["title"] == mock_url
    assert result["data"][CONF_SERVER] == "Plex Server 1"
    assert result["data"][CONF_SERVER_IDENTIFIER] == "unique_id_123"
    assert result["data"][PLEX_SERVER_CONFIG][CONF_URL] == mock_url
    assert result["data"][PLEX_SERVER_CONFIG][CONF_TOKEN] == MOCK_TOKEN

    # Complete Plex integration setup before teardown
    requests_mock.get(f"{mock_url}/library", text=empty_library)
    requests_mock.get(f"{mock_url}/library/sections", text=empty_payload)
    await hass.async_block_till_done()