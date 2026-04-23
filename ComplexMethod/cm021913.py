async def test_migration_2_1(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    sensor_entity_entry: er.RegistryEntry,
    sensor_device: dr.DeviceEntry,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test migration from v2.1 removes utility_meter config entry from device."""

    utility_meter_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "My utility meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": sensor_entity_entry.entity_id,
            "tariffs": tariffs,
        },
        title="My utility meter",
        version=2,
        minor_version=1,
    )
    utility_meter_config_entry.add_to_hass(hass)

    # Add the helper config entry to the device
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=utility_meter_config_entry.entry_id
    )

    # Check preconditions
    sensor_device = device_registry.async_get(sensor_device.id)
    assert utility_meter_config_entry.entry_id in sensor_device.config_entries

    await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    await hass.async_block_till_done()

    assert utility_meter_config_entry.state is ConfigEntryState.LOADED

    # Check that the helper config entry is removed from the device and the helper
    # entities are linked to the source device
    sensor_device = device_registry.async_get(sensor_device.id)
    assert utility_meter_config_entry.entry_id not in sensor_device.config_entries
    # Check that the entities are linked to the other device
    entities = set()
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        entities.add(utility_meter_entity.entity_id)
        assert utility_meter_entity.device_id == sensor_entity_entry.device_id
    assert entities == expected_entities

    assert utility_meter_config_entry.version == 2
    assert utility_meter_config_entry.minor_version == 2