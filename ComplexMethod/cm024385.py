async def test_form_abort_uuid_configured(hass: HomeAssistant, client) -> None:
    """Test abort if uuid is already configured, verify host update."""
    entry = await setup_webostv(hass, MOCK_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN][5:])
    assert entry.unique_id == MOCK_DISCOVERY_INFO.upnp[ATTR_UPNP_UDN][5:]
    assert entry.data[CONF_HOST] == HOST

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    user_config = {CONF_HOST: "new_host"}

    # Start another flow to make sure it aborts and updates host
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: config_entries.SOURCE_USER},
        data=user_config,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pairing"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "new_host"