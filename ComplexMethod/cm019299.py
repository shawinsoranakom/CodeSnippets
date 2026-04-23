async def test_config_flow(
    hass: HomeAssistant,
    group_type,
    group_state,
    member_state,
    member_attributes,
    extra_input,
    extra_options,
    extra_attrs,
) -> None:
    """Test the config flow."""
    members = [f"{group_type}.one", f"{group_type}.two"]
    for member in members:
        hass.states.async_set(member, member_state, member_attributes)

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

    with patch(
        "homeassistant.components.group.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Living Room",
                "entities": members,
                **extra_input,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room"
    assert result["data"] == {}
    assert result["options"] == {
        "entities": members,
        "group_type": group_type,
        "hide_members": False,
        "name": "Living Room",
        **extra_options,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "entities": members,
        "group_type": group_type,
        "hide_members": False,
        "name": "Living Room",
        **extra_options,
    }

    state = hass.states.get(f"{group_type}.living_room")
    assert state.state == group_state
    assert state.attributes["entity_id"] == members
    for key in extra_attrs:
        assert state.attributes[key] == extra_attrs[key]