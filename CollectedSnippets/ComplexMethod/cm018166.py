async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=voip.DOMAIN,
        data={},
        unique_id="1234",
    )
    config_entry.add_to_hass(hass)

    assert config_entry.options == {}

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Default
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"sip_port": 5060}

    # Manual
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sip_port": 5061},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"sip_port": 5061}

    # Manual with user
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sip_port": 5061, "sip_user": "HA"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"sip_port": 5061, "sip_user": "HA"}

    # Manual remove user
    result = await hass.config_entries.options.async_init(
        config_entry.entry_id,
    )

    assert config_entry.options == {"sip_port": 5061, "sip_user": "HA"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"sip_port": 5060, "sip_user": ""},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"sip_port": 5060}