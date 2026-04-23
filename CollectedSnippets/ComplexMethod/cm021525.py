async def test_options(
    hass: HomeAssistant,
    template_type: str,
    old_state_template: dict[str, Any],
    new_state_template: dict[str, Any],
    template_state: list[str],
    input_states: dict[str, Any],
    extra_options: dict[str, Any],
    options_options: dict[str, Any],
    key_template: str,
    suggested_device_class: str | None,
) -> None:
    """Test reconfiguring."""
    input_entities = ["one", "two"]

    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}", input_states[input_entity], {}
        )

    template_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My template",
            "template_type": template_type,
            **old_state_template,
            **extra_options,
        },
        title="My template",
    )
    template_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(template_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(f"{template_type}.my_template")
    assert state.state == template_state[0]

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == template_type
    assert get_schema_suggested_value(
        result["data_schema"].schema, key_template
    ) == old_state_template.get(key_template)
    assert "name" not in result["data_schema"].schema
    assert (
        get_schema_suggested_value(result["data_schema"].schema, "device_class")
        == suggested_device_class
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            **new_state_template,
            **options_options,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "name": "My template",
        "template_type": template_type,
        **new_state_template,
        **extra_options,
        **options_options,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My template",
        "template_type": template_type,
        **new_state_template,
        **extra_options,
        **options_options,
    }
    assert config_entry.title == "My template"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()
    state = hass.states.get(f"{template_type}.my_template")
    assert state.state == template_state[1]

    # Check we don't get suggestions from another entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": template_type},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == template_type

    assert get_schema_suggested_value(result["data_schema"].schema, "name") is None
    assert (
        get_schema_suggested_value(result["data_schema"].schema, key_template) is None
    )