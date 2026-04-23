async def test_setup_and_remove_config_entry(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    group_type: str,
    member_state: str,
    extra_options: dict[str, Any],
) -> None:
    """Test removing a config entry."""
    members1 = [f"{group_type}.one", f"{group_type}.two"]

    for member in members1:
        hass.states.async_set(member, member_state, {})

    # Setup the config entry
    group_config_entry = MockConfigEntry(
        data={},
        domain=group.DOMAIN,
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

    # Check the state and entity registry entry are present
    state = hass.states.get(f"{group_type}.bed_room")
    assert state.attributes["entity_id"] == members1
    assert entity_registry.async_get(f"{group_type}.bed_room") is not None

    # Remove the config entry
    assert await hass.config_entries.async_remove(group_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    assert hass.states.get(f"{group_type}.bed_room") is None
    assert entity_registry.async_get(f"{group_type}.bed_room") is None