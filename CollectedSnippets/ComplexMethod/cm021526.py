async def test_options_binary_sensor_remove_device_class(hass: HomeAssistant) -> None:
    """Test removing the binary sensor device class in options."""
    hass.states.async_set("binary_sensor.one", "on", {})
    hass.states.async_set("binary_sensor.two", "off", {})

    old_state_template = {
        "state": "{{ states('binary_sensor.one') == 'on' or states('binary_sensor.two') == 'on' }}"
    }
    new_state_template = {
        "state": "{{ states('binary_sensor.one') == 'on' and states('binary_sensor.two') == 'on' }}"
    }

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": "binary_sensor",
            **old_state_template,
            "device_class": "motion",
        },
        title="My template",
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "binary_sensor"
    assert (
        get_schema_suggested_value(result["data_schema"].schema, "device_class")
        == "motion"
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            **new_state_template,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "name": "My template",
        "template_type": "binary_sensor",
        **new_state_template,
    }
    assert config_entry.options == {
        "name": "My template",
        "template_type": "binary_sensor",
        **new_state_template,
    }
    assert "device_class" not in config_entry.options