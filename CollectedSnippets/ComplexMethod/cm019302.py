async def test_all_options(
    hass: HomeAssistant, group_type, extra_options, extra_options_after, advanced
) -> None:
    """Test reconfiguring."""
    members1 = [f"{group_type}.one", f"{group_type}.two"]
    members2 = [f"{group_type}.four", f"{group_type}.five"]

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

    assert hass.states.get(f"{group_type}.bed_room")

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    result = await hass.config_entries.options.async_init(
        config_entry.entry_id, context={"show_advanced_options": advanced}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == group_type

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": members2,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "entities": members2,
        "group_type": group_type,
        "hide_members": False,
        "name": "Bed Room",
        **extra_options_after,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "entities": members2,
        "group_type": group_type,
        "hide_members": False,
        "name": "Bed Room",
        **extra_options_after,
    }
    assert config_entry.title == "Bed Room"