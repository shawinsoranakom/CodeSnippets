async def test_speaker_options_flow(hass: HomeAssistant) -> None:
    """Test options config flow for speaker."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=MOCK_SPEAKER_CONFIG
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]

    result = await hass.config_entries.options.async_init(entry.entry_id, data=None)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={CONF_VOLUME_STEP: VOLUME_STEP}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == ""
    assert result["data"][CONF_VOLUME_STEP] == VOLUME_STEP
    assert CONF_APPS not in result["data"]