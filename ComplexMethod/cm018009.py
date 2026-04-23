async def test_reload_entry_entity_registry_works(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test we schedule an entry to be reloaded if disabled_by is updated."""
    handler = config_entries.EntityRegistryDisabledHandler(hass)
    handler.async_setup()

    config_entry = MockConfigEntry(
        domain="comp", state=config_entries.ConfigEntryState.LOADED
    )
    config_entry.supports_unload = True
    config_entry.add_to_hass(hass)
    mock_setup_entry = AsyncMock(return_value=True)
    mock_unload_entry = AsyncMock(return_value=True)
    mock_integration(
        hass,
        MockModule(
            "comp",
            async_setup_entry=mock_setup_entry,
            async_unload_entry=mock_unload_entry,
        ),
    )
    mock_platform(hass, "comp.config_flow", None)

    # Only changing disabled_by should update trigger
    entity_entry = entity_registry.async_get_or_create(
        "light", "hue", "123", config_entry=config_entry
    )
    entity_registry.async_update_entity(entity_entry.entity_id, name="yo")
    await hass.async_block_till_done()
    assert not handler.changed
    assert handler._remove_call_later is None

    # Disable entity, we should not do anything, only act when enabled.
    entity_registry.async_update_entity(
        entity_entry.entity_id, disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()
    assert not handler.changed
    assert handler._remove_call_later is None

    # Enable entity, check we are reloading config entry.
    entity_registry.async_update_entity(entity_entry.entity_id, disabled_by=None)
    await hass.async_block_till_done()
    assert handler.changed == {config_entry.entry_id}
    assert handler._remove_call_later is not None

    async_fire_time_changed(
        hass,
        dt_util.utcnow()
        + timedelta(seconds=config_entries.RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    assert len(mock_unload_entry.mock_calls) == 1