async def test_async_migrate_entries(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    entity_def: dict,
    ent_data: EntityMigrationData,
) -> None:
    """Test migration to new entity names."""
    mock_config_entry.add_to_hass(hass)

    device: dr.DeviceEntry = device_registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, MOCK_ADAPTER_MAC)},
    )

    TEST_EXISTING_ENTRY = {
        "domain": SENSOR_DOMAIN,
        "platform": DOMAIN,
        "unique_id": f"{MOCK_ADAPTER_MAC}_cya",
        "suggested_object_id": f"{MOCK_ADAPTER_NAME} CYA",
        "disabled_by": None,
        "has_entity_name": True,
        "original_name": "CYA",
    }

    entity_registry.async_get_or_create(
        **TEST_EXISTING_ENTRY, device_id=device.id, config_entry=mock_config_entry
    )

    entity: er.RegistryEntry = entity_registry.async_get_or_create(
        **entity_def, device_id=device.id, config_entry=mock_config_entry
    )

    old_eid = f"{ent_data.domain}.{slugify(f'{MOCK_ADAPTER_NAME} {ent_data.old_name}')}"
    old_uid = f"{MOCK_ADAPTER_MAC}_{ent_data.old_key}"
    new_eid = f"{ent_data.domain}.{slugify(f'{MOCK_ADAPTER_NAME} {ent_data.new_name}')}"
    new_uid = f"{MOCK_ADAPTER_MAC}_{ent_data.new_key}"

    assert entity.unique_id == old_uid
    assert entity.entity_id == old_eid

    with (
        patch(
            GATEWAY_DISCOVERY_IMPORT_PATH,
            return_value={},
        ),
        patch.multiple(
            ScreenLogicGateway,
            async_connect=_migration_connect,
            is_connected=True,
            _async_connected_request=DEFAULT,
        ),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    entity_migrated = entity_registry.async_get(new_eid)
    assert entity_migrated
    assert entity_migrated.entity_id == new_eid
    assert entity_migrated.unique_id == new_uid
    assert entity_migrated.original_name == ent_data.new_name