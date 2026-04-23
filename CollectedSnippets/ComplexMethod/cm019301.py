async def test_options(
    hass: HomeAssistant, group_type, member_state, extra_options, options_options
) -> None:
    """Test reconfiguring."""
    members1 = [f"{group_type}.one", f"{group_type}.two"]
    members2 = [f"{group_type}.four", f"{group_type}.five"]

    for member in members1:
        hass.states.async_set(member, member_state, {})
    for member in members2:
        hass.states.async_set(member, member_state, {})

    group_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": members1,
            "group_type": group_type,
            "name": "Bed Room",
            **extra_options,
        },
        title="Bed Room",
    )
    group_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(group_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(f"{group_type}.bed_room")
    assert state.attributes["entity_id"] == members1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == group_type
    assert (
        get_schema_suggested_value(result["data_schema"].schema, "entities") == members1
    )
    assert "name" not in result["data_schema"].schema
    assert result["data_schema"].schema["entities"].config["exclude_entities"] == [
        f"{group_type}.bed_room"
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"entities": members2, **options_options},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "entities": members2,
        "group_type": group_type,
        "hide_members": False,
        "name": "Bed Room",
        **extra_options,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "entities": members2,
        "group_type": group_type,
        "hide_members": False,
        "name": "Bed Room",
        **extra_options,
    }
    assert config_entry.title == "Bed Room"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()
    state = hass.states.get(f"{group_type}.bed_room")
    assert state.attributes["entity_id"] == members2

    # Check we don't get suggestions from another entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": group_type},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == group_type

    assert get_schema_suggested_value(result["data_schema"].schema, "entities") is None
    assert get_schema_suggested_value(result["data_schema"].schema, "name") is None