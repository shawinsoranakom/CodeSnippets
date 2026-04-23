async def test_async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    generic_thermostat_config_entry: MockConfigEntry,
    switch_entity_entry: er.RegistryEntry,
    source_entity_id: str,
    expected_helper_device_id: str | None,
    expected_events: list[str],
) -> None:
    """Test the generic_thermostat config entry is removed when the source entity is removed."""
    source_entity_entry = entity_registry.async_get(source_entity_id)

    assert await hass.config_entries.async_setup(
        generic_thermostat_config_entry.entry_id
    )
    await hass.async_block_till_done()

    generic_thermostat_entity_entry = entity_registry.async_get(
        "climate.my_generic_thermostat"
    )
    assert generic_thermostat_entity_entry.device_id == switch_entity_entry.device_id

    source_device = device_registry.async_get(source_entity_entry.device_id)
    assert generic_thermostat_config_entry.entry_id not in source_device.config_entries

    events = track_entity_registry_actions(
        hass, generic_thermostat_entity_entry.entity_id
    )

    # Remove the source entity's config entry from the device, this removes the
    # source entity
    with patch(
        "homeassistant.components.generic_thermostat.async_unload_entry",
        wraps=generic_thermostat.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            source_device.id, remove_config_entry_id=source_entity_entry.config_entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    # Check that the helper entity is linked to the expected source device
    generic_thermostat_entity_entry = entity_registry.async_get(
        "climate.my_generic_thermostat"
    )
    assert generic_thermostat_entity_entry.device_id == expected_helper_device_id

    # Check that the device is removed
    assert not device_registry.async_get(source_device.id)

    # Check that the generic_thermostat config entry is not removed
    assert (
        generic_thermostat_config_entry.entry_id
        in hass.config_entries.async_entry_ids()
    )

    # Check we got the expected events
    assert events == expected_events