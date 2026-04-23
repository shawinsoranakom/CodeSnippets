async def test_user_web_login(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    solaredge_web_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user config with web login."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: NAME,
            CONF_SITE_ID: SITE_ID,
            CONF_SECTION_API_AUTH: {CONF_API_KEY: ""},
            CONF_SECTION_WEB_AUTH: {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "solaredge_site_1_2_3"

    data = result.get("data")
    assert data
    assert data[CONF_SITE_ID] == SITE_ID
    assert data[CONF_USERNAME] == USERNAME
    assert data[CONF_PASSWORD] == PASSWORD
    assert CONF_API_KEY not in data

    assert len(mock_setup_entry.mock_calls) == 1
    solaredge_web_api.async_get_equipment.assert_awaited_once()