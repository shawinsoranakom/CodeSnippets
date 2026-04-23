async def test_options_flow_hides_members(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    group_type,
    extra_input,
    hide_members,
    hidden_by_initial,
    hidden_by,
) -> None:
    """Test the options flow hides or unhides members if requested."""
    fake_uuid = "a266a680b608c32770e6c45bfe6b8411"
    entry = entity_registry.async_get_or_create(
        group_type,
        "test",
        "unique1",
        suggested_object_id="one",
        hidden_by=hidden_by_initial,
    )
    assert entry.entity_id == f"{group_type}.one"

    entry = entity_registry.async_get_or_create(
        group_type,
        "test",
        "unique3",
        suggested_object_id="three",
        hidden_by=hidden_by_initial,
    )
    assert entry.entity_id == f"{group_type}.three"

    members = [f"{group_type}.one", f"{group_type}.two", fake_uuid, entry.id]

    group_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entities": members,
            "group_type": group_type,
            "hide_members": False,
            "name": "Bed Room",
            **extra_input,
        },
        title="Bed Room",
    )
    group_config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(group_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(group_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entities": members,
            "hide_members": hide_members,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert entity_registry.async_get(f"{group_type}.one").hidden_by == hidden_by
    assert entity_registry.async_get(f"{group_type}.three").hidden_by == hidden_by