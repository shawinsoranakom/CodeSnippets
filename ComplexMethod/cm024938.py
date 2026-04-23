async def test_migration_1_11(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test migration from version 1.11.

    This is the first version which has deleted entities, make sure deleted entities
    are updated.
    """
    hass_storage[er.STORAGE_KEY] = {
        "version": 1,
        "minor_version": 11,
        "data": {
            "entities": [
                {
                    "aliases": [],
                    "area_id": None,
                    "capabilities": {},
                    "config_entry_id": None,
                    "device_id": None,
                    "disabled_by": None,
                    "entity_category": None,
                    "entity_id": "test.entity",
                    "has_entity_name": False,
                    "hidden_by": None,
                    "icon": None,
                    "id": "12345",
                    "modified_at": "1970-01-01T00:00:00+00:00",
                    "name": None,
                    "options": {},
                    "original_device_class": "best_class",
                    "original_icon": None,
                    "original_name": None,
                    "platform": "super_platform",
                    "supported_features": 0,
                    "translation_key": None,
                    "unique_id": "very_unique",
                    "unit_of_measurement": None,
                    "device_class": None,
                }
            ],
            "deleted_entities": [
                {
                    "config_entry_id": None,
                    "entity_id": "test.deleted_entity",
                    "id": "23456",
                    "orphaned_timestamp": None,
                    "platform": "super_duper_platform",
                    "unique_id": "very_very_unique",
                }
            ],
        },
    }

    await er.async_load(hass)
    registry = er.async_get(hass)

    entry = registry.async_get_or_create("test", "super_platform", "very_unique")

    assert entry.device_class is None
    assert entry.original_device_class == "best_class"

    deleted_entry = registry.deleted_entities[
        ("test", "super_duper_platform", "very_very_unique")
    ]
    assert deleted_entry.disabled_by is UNDEFINED
    assert deleted_entry.hidden_by is UNDEFINED
    assert deleted_entry.options is UNDEFINED

    # Check migrated data
    await flush_store(registry._store)
    migrated_data = hass_storage[er.STORAGE_KEY]
    assert migrated_data == {
        "version": er.STORAGE_VERSION_MAJOR,
        "minor_version": er.STORAGE_VERSION_MINOR,
        "key": er.STORAGE_KEY,
        "data": {
            "entities": [
                {
                    "aliases": [],
                    "aliases_v2": [None],
                    "area_id": None,
                    "capabilities": {},
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "1970-01-01T00:00:00+00:00",
                    "device_id": None,
                    "disabled_by": None,
                    "entity_category": None,
                    "entity_id": "test.entity",
                    "has_entity_name": False,
                    "hidden_by": None,
                    "icon": None,
                    "id": ANY,
                    "labels": [],
                    "modified_at": "1970-01-01T00:00:00+00:00",
                    "name": None,
                    "object_id_base": None,
                    "options": {},
                    "original_device_class": "best_class",
                    "original_icon": None,
                    "original_name": None,
                    "platform": "super_platform",
                    "previous_unique_id": None,
                    "suggested_object_id": None,
                    "supported_features": 0,
                    "translation_key": None,
                    "unique_id": "very_unique",
                    "unit_of_measurement": None,
                    "device_class": None,
                }
            ],
            "deleted_entities": [
                {
                    "aliases": [],
                    "aliases_v2": [None],
                    "area_id": None,
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "1970-01-01T00:00:00+00:00",
                    "device_class": None,
                    "disabled_by": None,
                    "disabled_by_undefined": True,
                    "entity_id": "test.deleted_entity",
                    "hidden_by": None,
                    "hidden_by_undefined": True,
                    "icon": None,
                    "id": "23456",
                    "labels": [],
                    "modified_at": "1970-01-01T00:00:00+00:00",
                    "name": None,
                    "options": {},
                    "options_undefined": True,
                    "orphaned_timestamp": None,
                    "platform": "super_duper_platform",
                    "unique_id": "very_very_unique",
                }
            ],
        },
    }

    # Serialize the migrated data again
    registry.async_schedule_save()
    await flush_store(registry._store)
    assert hass_storage[er.STORAGE_KEY] == migrated_data