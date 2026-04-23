async def test_reload_migration_with_leading_zero_mac(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    responses: list[AiohttpClientMockResponse],
) -> None:
    """Test migration and reload of a device with a mac address with a leading zero."""
    mac_address = "01:02:03:04:05:06"
    mac_address_unique_id = dr.format_mac(mac_address)
    serial_number = "0"

    # Setup the config entry to be in a pre-migrated state
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=serial_number,
        data={
            "host": "127.0.0.1",
            "password": "password",
            CONF_MAC: mac_address,
            "serial_number": serial_number,
        },
    )
    config_entry.add_to_hass(hass)

    # This test sets up and then reloads the config entry, so we need a second
    # copy of the default response sequence.
    responses.extend([*responses])

    # Create a device and entity with the old unique id format
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, f"{serial_number}-1")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "switch",
        DOMAIN,
        f"{serial_number}-1-zone1",
        suggested_object_id="zone1",
        config_entry=config_entry,
        device_id=device_entry.id,
    )

    # Setup the integration, which will migrate the unique ids
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify the device and entity were migrated to the new format
    migrated_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, f"{mac_address_unique_id}-1")}
    )
    assert migrated_device_entry is not None
    migrated_entity_entry = entity_registry.async_get(entity_entry.entity_id)
    assert migrated_entity_entry is not None
    assert migrated_entity_entry.unique_id == f"{mac_address_unique_id}-1-zone1"

    # Reload the integration
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify the device and entity still have the correct identifiers and were not duplicated
    reloaded_device_entry = device_registry.async_get(migrated_device_entry.id)
    assert reloaded_device_entry is not None
    assert reloaded_device_entry.identifiers == {(DOMAIN, f"{mac_address_unique_id}-1")}
    reloaded_entity_entry = entity_registry.async_get(entity_entry.entity_id)
    assert reloaded_entity_entry is not None
    assert reloaded_entity_entry.unique_id == f"{mac_address_unique_id}-1-zone1"

    assert (
        len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id))
        == 1
    )
    assert (
        len(er.async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 1
    )