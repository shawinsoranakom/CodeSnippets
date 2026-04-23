async def test_homekit_discovery(
    hass: HomeAssistant,
    mock_roku_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the homekit discovery flow."""
    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_HOMEKIT}, data=discovery_info
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {CONF_NAME: NAME_ROKUTV}

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME_ROKUTV

    assert "data" in result
    assert result["data"][CONF_HOST] == HOMEKIT_HOST
    assert result["data"][CONF_NAME] == NAME_ROKUTV

    # test abort on existing host
    discovery_info = dataclasses.replace(MOCK_HOMEKIT_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_HOMEKIT}, data=discovery_info
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"