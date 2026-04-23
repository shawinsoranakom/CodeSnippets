async def test_user_api_key(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    solaredge_api: Mock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user config with API key."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: NAME,
            CONF_SITE_ID: SITE_ID,
            CONF_SECTION_API_AUTH: {CONF_API_KEY: API_KEY},
            CONF_SECTION_WEB_AUTH: {
                CONF_USERNAME: "",
                CONF_PASSWORD: "",
            },
        },
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "solaredge_site_1_2_3"

    data = result.get("data")
    assert data
    assert data[CONF_SITE_ID] == SITE_ID
    assert data[CONF_API_KEY] == API_KEY
    assert CONF_USERNAME not in data
    assert CONF_PASSWORD not in data

    assert len(mock_setup_entry.mock_calls) == 1