async def test_config_flow_hides_members(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    group_type,
    extra_input,
    hide_members,
    hidden_by,
) -> None:
    """Test the config flow hides members if requested."""
    fake_uuid = "a266a680b608c32770e6c45bfe6b8411"
    entry = entity_registry.async_get_or_create(
        group_type, "test", "unique", suggested_object_id="one"
    )
    assert entry.entity_id == f"{group_type}.one"
    assert entry.hidden_by is None

    entry = entity_registry.async_get_or_create(
        group_type, "test", "unique3", suggested_object_id="three"
    )
    assert entry.entity_id == f"{group_type}.three"
    assert entry.hidden_by is None

    members = [f"{group_type}.one", f"{group_type}.two", fake_uuid, entry.id]
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

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "name": "Living Room",
            "entities": members,
            "hide_members": hide_members,
            **extra_input,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert entity_registry.async_get(f"{group_type}.one").hidden_by == hidden_by
    assert entity_registry.async_get(f"{group_type}.three").hidden_by == hidden_by