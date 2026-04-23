async def test_options(
    hass: HomeAssistant,
    target_domain: Platform,
) -> None:
    """Test reconfiguring."""
    switch_state = STATE_ON
    hass.states.async_set("switch.ceiling", switch_state)
    switch_as_x_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.ceiling",
            CONF_INVERT: True,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    switch_as_x_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(f"{target_domain}.abc")
    assert state.state == STATE_MAP[True][target_domain][switch_state]

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert get_schema_suggested_value(result["data_schema"].schema, CONF_INVERT) is True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_INVERT: False,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ENTITY_ID: "switch.ceiling",
        CONF_INVERT: False,
        CONF_TARGET_DOMAIN: target_domain,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        CONF_ENTITY_ID: "switch.ceiling",
        CONF_INVERT: False,
        CONF_TARGET_DOMAIN: target_domain,
    }
    assert config_entry.title == "ABC"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 2

    # Check the state of the entity has changed as expected
    state = hass.states.get(f"{target_domain}.abc")
    assert state.state == STATE_MAP[False][target_domain][switch_state]