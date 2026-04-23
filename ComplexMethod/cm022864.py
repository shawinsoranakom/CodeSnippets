async def test_automatic_registry_cleanup(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    tankerkoenig: AsyncMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test automatic registry cleanup for obsolete entity and devices entries."""
    # setup normal
    config_entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    assert (
        len(er.async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 4
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id))
        == 1
    )

    # add obsolete entity and device entries
    obsolete_station_id = "aabbccddee-xxxx-xxxx-xxxx-ff11223344"

    entity_registry.async_get_or_create(
        DOMAIN,
        BINARY_SENSOR_DOMAIN,
        f"{obsolete_station_id}_status",
        config_entry=config_entry,
    )
    entity_registry.async_get_or_create(
        DOMAIN,
        SENSOR_DOMAIN,
        f"{obsolete_station_id}_e10",
        config_entry=config_entry,
    )
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(ATTR_ID, obsolete_station_id)},
        name="Obsolete Station",
    )

    assert (
        len(er.async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 6
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id))
        == 2
    )

    # reload config entry to trigger automatic cleanup
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        len(er.async_entries_for_config_entry(entity_registry, config_entry.entry_id))
        == 4
    )
    assert (
        len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id))
        == 1
    )