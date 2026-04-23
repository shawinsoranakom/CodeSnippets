async def test_user_legacy(
    hass: HomeAssistant, connect_legacy, patch_setup_entry, unique_id
) -> None:
    """Test user config."""
    flow_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "show_advanced_options": True}
    )
    assert flow_result["type"] is FlowResultType.FORM
    assert flow_result["step_id"] == "user"

    connect_legacy.return_value.async_get_nvram.return_value = unique_id

    # test with all provided
    legacy_result = await hass.config_entries.flow.async_configure(
        flow_result["flow_id"], user_input=CONFIG_DATA_TELNET
    )
    await hass.async_block_till_done()

    assert legacy_result["type"] is FlowResultType.FORM
    assert legacy_result["step_id"] == "legacy"

    # complete configuration
    result = await hass.config_entries.flow.async_configure(
        legacy_result["flow_id"], user_input={CONF_MODE: MODE_AP}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"] == {**CONFIG_DATA_TELNET, CONF_MODE: MODE_AP}

    assert len(patch_setup_entry.mock_calls) == 1