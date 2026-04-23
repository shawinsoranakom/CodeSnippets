async def test_migrate_config_entry(
    hass: HomeAssistant,
    minor_version: int,
    suffix: str,
    device_registry: DeviceRegistry,
    entity_registry: EntityRegistry,
    mock_solarlog_connector: AsyncMock,
) -> None:
    """Test successful migration of entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=HOST,
        data={
            CONF_HOST: HOST,
        },
        version=1,
        minor_version=minor_version,
    )
    entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Solar-Log",
        name="solarlog",
    )
    uid = f"{entry.entry_id}_{suffix}"

    sensor_entity = entity_registry.async_get_or_create(
        config_entry=entry,
        platform=DOMAIN,
        domain=Platform.SENSOR,
        unique_id=uid,
        device_id=device.id,
    )

    assert entry.version == 1
    assert entry.minor_version == minor_version
    assert sensor_entity.unique_id == f"{entry.entry_id}_{suffix}"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(sensor_entity.entity_id)
    assert entity_migrated
    assert entity_migrated.unique_id == f"{entry.entry_id}_last_updated"

    assert entry.version == 1
    assert entry.minor_version == 3
    assert entry.data[CONF_HOST] == HOST
    assert entry.data[CONF_HAS_PWD] is False