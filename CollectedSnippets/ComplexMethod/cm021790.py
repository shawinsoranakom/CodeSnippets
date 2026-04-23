async def test_tv_options_flow_no_apps(hass: HomeAssistant) -> None:
    """Test options config flow for TV without providing apps option."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_USER_VALID_TV_CONFIG
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    options = {CONF_VOLUME_STEP: VOLUME_STEP}
    options.update(MOCK_INCLUDE_NO_APPS)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=options
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS not in result["data"]