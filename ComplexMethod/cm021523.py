async def test_config_flow(
    hass: HomeAssistant,
    template_type: str,
    state_template: dict[str, Any],
    template_state: str,
    input_states: dict[str, Any],
    input_attributes: dict[str, Any],
    extra_input: dict[str, Any],
    extra_options: dict[str, Any],
    extra_attrs: dict[str, Any],
) -> None:
    """Test the config flow."""
    input_entities = ["one", "two"]
    for input_entity in input_entities:
        hass.states.async_set(
            f"{template_type}.{input_entity}",
            input_states[input_entity],
            input_attributes.get(input_entity, {}),
        )

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

    availability = {"advanced_options": {"availability": "{{ True }}"}}

    with patch(
        "homeassistant.components.template.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "My template", **state_template, **extra_input, **availability},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My template"
    assert result["data"] == {}
    assert result["options"] == {
        "name": "My template",
        "template_type": template_type,
        **state_template,
        **extra_options,
        **availability,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My template",
        "template_type": template_type,
        **state_template,
        **extra_options,
        **availability,
    }

    state = hass.states.get(f"{template_type}.my_template")
    assert state.state == template_state
    for key, value in extra_attrs.items():
        assert state.attributes[key] == value