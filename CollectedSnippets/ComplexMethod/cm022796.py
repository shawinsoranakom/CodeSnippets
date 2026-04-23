async def test_entity_registry_events(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    switch_entity_registry_entry: er.RegistryEntry,
    switch_as_x_config_entry: MockConfigEntry,
    target_domain: str,
    state_on: str,
    state_off: str,
) -> None:
    """Test entity registry events are tracked."""
    switch_entity_id = switch_entity_registry_entry.entity_id
    hass.states.async_set(switch_entity_id, STATE_ON)

    assert await hass.config_entries.async_setup(switch_as_x_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(f"{target_domain}.abc").state == state_on

    # Change entity_id
    new_switch_entity_id = f"{switch_entity_id}_new"
    entity_registry.async_update_entity(
        switch_entity_id, new_entity_id=new_switch_entity_id
    )
    hass.states.async_set(new_switch_entity_id, STATE_OFF)
    await hass.async_block_till_done()

    # Check tracking the new entity_id
    await hass.async_block_till_done()
    assert hass.states.get(f"{target_domain}.abc").state == state_off

    # The old entity_id should no longer be tracked
    hass.states.async_set(switch_entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get(f"{target_domain}.abc").state == state_off

    # Check changing name does not reload the config entry
    with patch(
        "homeassistant.components.switch_as_x.async_unload_entry",
    ) as mock_setup_entry:
        entity_registry.async_update_entity(new_switch_entity_id, name="New name")
        await hass.async_block_till_done()
    mock_setup_entry.assert_not_called()

    # Check removing the entity removes the config entry
    entity_registry.async_remove(new_switch_entity_id)
    await hass.async_block_till_done()

    assert hass.states.get(f"{target_domain}.abc") is None
    assert entity_registry.async_get(f"{target_domain}.abc") is None
    assert len(hass.config_entries.async_entries("switch_as_x")) == 0