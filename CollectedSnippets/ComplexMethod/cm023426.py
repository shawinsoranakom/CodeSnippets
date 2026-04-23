async def test_ssdp_discovery(
    hass: HomeAssistant,
    mock_roku_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the SSDP discovery flow."""
    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {CONF_NAME: UPNP_FRIENDLY_NAME}

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == UPNP_FRIENDLY_NAME

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_NAME] == UPNP_FRIENDLY_NAME