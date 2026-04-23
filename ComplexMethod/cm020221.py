async def test_options_flow_http(hass: HomeAssistant, patch_setup_entry) -> None:
    """Test config flow options for http mode."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={**CONFIG_DATA_HTTP, CONF_MODE: MODE_ROUTER},
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert CONF_INTERFACE not in result["data_schema"].schema
    assert CONF_DNSMASQ not in result["data_schema"].schema
    assert CONF_REQUIRE_IP not in result["data_schema"].schema

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_CONSIDER_HOME: 20,
            CONF_TRACK_UNKNOWN: True,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_CONSIDER_HOME: 20,
        CONF_TRACK_UNKNOWN: True,
    }