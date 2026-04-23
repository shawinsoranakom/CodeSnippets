async def test_unhide_members_on_remove(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    group_type: str,
    extra_options: dict[str, Any],
    hide_members: bool,
    hidden_by_initial: er.RegistryEntryHider,
    hidden_by: str,
) -> None:
    """Test removing a config entry."""
    entry1 = entity_registry.async_get_or_create(
        group_type,
        "test",
        "unique1",
        suggested_object_id="one",
        hidden_by=hidden_by_initial,
    )
    assert entry1.entity_id == f"{group_type}.one"

    entry3 = entity_registry.async_get_or_create(
        group_type,
        "test",
        "unique3",
        suggested_object_id="three",
        hidden_by=hidden_by_initial,
    )
    assert entry3.entity_id == f"{group_type}.three"

    entry4 = entity_registry.async_get_or_create(
        group_type,
        "test",
        "unique4",
        suggested_object_id="four",
    )
    assert entry4.entity_id == f"{group_type}.four"

    members = [f"{group_type}.one", f"{group_type}.two", entry3.id, entry4.id]

    # Setup the config entry
    group_config_entry = MockConfigEntry(
        data={},
        domain=group.DOMAIN,
        options={
            "entities": members,
            "group_type": group_type,
            "hide_members": hide_members,
            "name": "Bed Room",
            **extra_options,
        },
        title="Bed Room",
    )
    group_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(group_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state is present
    assert hass.states.get(f"{group_type}.bed_room")

    # Remove one entity registry entry, to make sure this does not trip up config entry
    # removal
    entity_registry.async_remove(entry4.entity_id)

    # Remove the config entry
    assert await hass.config_entries.async_remove(group_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the group members are unhidden
    assert entity_registry.async_get(f"{group_type}.one").hidden_by == hidden_by
    assert entity_registry.async_get(f"{group_type}.three").hidden_by == hidden_by