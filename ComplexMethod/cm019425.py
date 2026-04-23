async def test_user_both_auth(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    solaredge_api: Mock,
    solaredge_web_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user config with both API key and web login."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: NAME,
            CONF_SITE_ID: SITE_ID,
            CONF_SECTION_API_AUTH: {CONF_API_KEY: API_KEY},
            CONF_SECTION_WEB_AUTH: {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    data = result.get("data")
    assert data
    assert data[CONF_SITE_ID] == SITE_ID
    assert data[CONF_API_KEY] == API_KEY
    assert data[CONF_USERNAME] == USERNAME
    assert data[CONF_PASSWORD] == PASSWORD

    assert len(mock_setup_entry.mock_calls) == 1