async def test_load_bad_data(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test loading invalid data."""
    hass_storage[er.STORAGE_KEY] = {
        "version": er.STORAGE_VERSION_MAJOR,
        "minor_version": er.STORAGE_VERSION_MINOR,
        "data": {
            "entities": [
                {
                    "aliases": [],
                    "aliases_v2": [],
                    "area_id": None,
                    "capabilities": None,
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "2024-02-14T12:00:00.900075+00:00",
                    "device_class": None,
                    "device_id": None,
                    "disabled_by": None,
                    "entity_category": None,
                    "entity_id": "test.test1",
                    "has_entity_name": False,
                    "hidden_by": None,
                    "icon": None,
                    "id": "00001",
                    "labels": [],
                    "modified_at": "2024-02-14T12:00:00.900075+00:00",
                    "name": None,
                    "object_id_base": None,
                    "options": None,
                    "original_device_class": None,
                    "original_icon": None,
                    "original_name": None,
                    "platform": "super_platform",
                    "previous_unique_id": None,
                    "suggested_object_id": None,
                    "supported_features": 0,
                    "translation_key": None,
                    "unique_id": 123,  # Should trigger warning
                    "unit_of_measurement": None,
                },
                {
                    "aliases": [],
                    "aliases_v2": [],
                    "area_id": None,
                    "capabilities": None,
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "2024-02-14T12:00:00.900075+00:00",
                    "device_class": None,
                    "device_id": None,
                    "disabled_by": None,
                    "entity_category": None,
                    "entity_id": "test.test2",
                    "has_entity_name": False,
                    "hidden_by": None,
                    "icon": None,
                    "id": "00002",
                    "labels": [],
                    "modified_at": "2024-02-14T12:00:00.900075+00:00",
                    "name": None,
                    "object_id_base": None,
                    "options": None,
                    "original_device_class": None,
                    "original_icon": None,
                    "original_name": None,
                    "platform": "super_platform",
                    "previous_unique_id": None,
                    "suggested_object_id": None,
                    "supported_features": 0,
                    "translation_key": None,
                    "unique_id": ["not", "valid"],  # Should not load
                    "unit_of_measurement": None,
                },
            ],
            "deleted_entities": [
                {
                    "aliases": [],
                    "aliases_v2": [],
                    "area_id": None,
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "2024-02-14T12:00:00.900075+00:00",
                    "device_class": None,
                    "disabled_by": None,
                    "disabled_by_undefined": False,
                    "entity_id": "test.test3",
                    "hidden_by": None,
                    "hidden_by_undefined": False,
                    "icon": None,
                    "id": "00003",
                    "labels": [],
                    "modified_at": "2024-02-14T12:00:00.900075+00:00",
                    "name": None,
                    "options": None,
                    "options_undefined": False,
                    "orphaned_timestamp": None,
                    "platform": "super_platform",
                    "unique_id": 234,  # Should not load
                },
                {
                    "aliases": [],
                    "aliases_v2": [],
                    "area_id": None,
                    "categories": {},
                    "config_entry_id": None,
                    "config_subentry_id": None,
                    "created_at": "2024-02-14T12:00:00.900075+00:00",
                    "device_class": None,
                    "disabled_by": None,
                    "disabled_by_undefined": False,
                    "entity_id": "test.test4",
                    "hidden_by": None,
                    "hidden_by_undefined": False,
                    "icon": None,
                    "id": "00004",
                    "labels": [],
                    "modified_at": "2024-02-14T12:00:00.900075+00:00",
                    "name": None,
                    "options": None,
                    "options_undefined": False,
                    "orphaned_timestamp": None,
                    "platform": "super_platform",
                    "unique_id": ["also", "not", "valid"],  # Should not load
                },
            ],
        },
    }

    await er.async_load(hass)
    registry = er.async_get(hass)

    assert len(registry.entities) == 1
    assert set(registry.entities.keys()) == {"test.test1"}

    assert len(registry.deleted_entities) == 1
    assert set(registry.deleted_entities.keys()) == {("test", "super_platform", 234)}

    assert (
        "'test' from integration super_platform has a non string unique_id '123', "
        "please create a bug report" not in caplog.text
    )
    assert (
        "'test' from integration super_platform has a non string unique_id '234', "
        "please create a bug report" not in caplog.text
    )
    assert (
        "Entity registry entry 'test.test2' from integration super_platform could not "
        "be loaded: 'unique_id must be a string, got ['not', 'valid']', please create "
        "a bug report" in caplog.text
    )