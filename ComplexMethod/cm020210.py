async def test_successful_config_flow(
    hass: HomeAssistant,
    owm_client_mock: AsyncMock,
) -> None:
    """Test that the form is served with valid input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # create entry
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"][CONF_LATITUDE] == USER_INPUT[CONF_LOCATION][CONF_LATITUDE]
    assert result["data"][CONF_LONGITUDE] == USER_INPUT[CONF_LOCATION][CONF_LONGITUDE]
    assert result["data"][CONF_API_KEY] == USER_INPUT[CONF_API_KEY]

    # validate entry state
    conf_entries = hass.config_entries.async_entries(DOMAIN)
    entry = conf_entries[0]
    assert entry.state is ConfigEntryState.LOADED

    # unload entry
    await hass.config_entries.async_unload(conf_entries[0].entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED