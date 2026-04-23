async def test_update_entity(
    hass: HomeAssistant, client: MockHAClientWebSocket, freezer: FrozenDateTimeFactory
) -> None:
    """Test updating entity."""
    created = datetime.fromisoformat("2024-02-14T12:00:00.900075+00:00")
    freezer.move_to(created)
    registry = mock_registry(
        hass,
        {
            "test_domain.world": RegistryEntryWithDefaults(
                entity_id="test_domain.world",
                unique_id="1234",
                # Using component.async_add_entities is equal to platform "domain"
                platform="test_platform",
                name="before update",
                icon="icon:before update",
            )
        },
    )
    platform = MockEntityPlatform(hass)
    entity = MockEntity(unique_id="1234")
    await platform.async_add_entities([entity])

    state = hass.states.get("test_domain.world")
    assert state is not None
    assert state.name == "before update"
    assert state.attributes[ATTR_ICON] == "icon:before update"

    modified = datetime.fromisoformat("2024-07-17T13:30:00.900075+00:00")
    freezer.move_to(modified)

    # Update area, categories, device_class, hidden_by, icon, labels & name
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "categories": {"scope1": "id", "scope2": "id"},
            "device_class": "custom_device_class",
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "labels": ["label1", "label2"],
            "name": "after update",
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope2": "id"},
            "created_at": created.timestamp(),
            "config_entry_id": None,
            "config_subentry_id": None,
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        }
    }

    state = hass.states.get("test_domain.world")
    assert state.name == "after update"
    assert state.attributes[ATTR_ICON] == "icon:after update"

    modified = datetime.fromisoformat("2024-07-20T00:00:00.900075+00:00")
    freezer.move_to(modified)

    # Update hidden_by to illegal value
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "hidden_by": "ivy",
        }
    )

    msg = await client.receive_json()
    assert not msg["success"]

    assert registry.entities["test_domain.world"].hidden_by is RegistryEntryHider.USER

    # Update disabled_by to user
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": "user",  # We exchange strings over the WS API, not enums
        }
    )

    msg = await client.receive_json()
    assert msg["success"]

    assert hass.states.get("test_domain.world") is None
    entry = registry.entities["test_domain.world"]
    assert entry.disabled_by is RegistryEntryDisabler.USER
    assert entry.created_at == created
    assert entry.modified_at == modified

    modified = datetime.fromisoformat("2024-07-21T00:00:00.900075+00:00")
    freezer.move_to(modified)

    # Update disabled_by to None
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "disabled_by": None,
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope2": "id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
        "require_restart": True,
    }

    modified = datetime.fromisoformat("2024-07-22T00:00:00.900075+00:00")
    freezer.move_to(modified)

    # Update entity option
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "options_domain": "sensor",
            "options": {"unit_of_measurement": "beard_second"},
        }
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope2": "id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {"sensor": {"unit_of_measurement": "beard_second"}},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
    }

    modified = datetime.fromisoformat("2024-07-23T00:00:00.900075+00:00")
    freezer.move_to(modified)

    # Add a category to the entity
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "categories": {"scope3": "id"},
        }
    )

    msg = await client.receive_json()
    assert msg["success"]

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope2": "id", "scope3": "id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {"sensor": {"unit_of_measurement": "beard_second"}},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
    }

    modified = datetime.fromisoformat("2024-07-24T00:00:00.900075+00:00")
    freezer.move_to(modified)

    # Move the entity to a different category
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "categories": {"scope3": "other_id"},
        }
    )

    msg = await client.receive_json()
    assert msg["success"]

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope2": "id", "scope3": "other_id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {"sensor": {"unit_of_measurement": "beard_second"}},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
    }

    modified = datetime.fromisoformat("2024-07-23T10:00:00.900075+00:00")
    freezer.move_to(modified)

    # Move the entity to a different category
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "categories": {"scope2": None},
        }
    )

    msg = await client.receive_json()
    assert msg["success"]

    assert msg["result"] == {
        "entity_entry": {
            "aliases": ["alias_1", "alias_2"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope3": "other_id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {"sensor": {"unit_of_measurement": "beard_second"}},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
    }

    # Add illegal terms to aliases
    await client.send_json_auto_id(
        {
            "type": "config/entity_registry/update",
            "entity_id": "test_domain.world",
            "aliases": [None, "alias_1", "alias_2", "", " alias_3 ", " "],
        }
    )

    msg = await client.receive_json()
    assert msg["success"]

    assert msg["result"] == {
        "entity_entry": {
            "aliases": [None, "alias_1", "alias_2", "alias_3"],
            "area_id": "mock-area-id",
            "capabilities": None,
            "categories": {"scope1": "id", "scope3": "other_id"},
            "config_entry_id": None,
            "config_subentry_id": None,
            "created_at": created.timestamp(),
            "device_class": "custom_device_class",
            "device_id": None,
            "disabled_by": None,
            "entity_category": None,
            "entity_id": "test_domain.world",
            "has_entity_name": False,
            "hidden_by": "user",  # We exchange strings over the WS API, not enums
            "icon": "icon:after update",
            "id": ANY,
            "labels": unordered(["label1", "label2"]),
            "modified_at": modified.timestamp(),
            "name": "after update",
            "options": {"sensor": {"unit_of_measurement": "beard_second"}},
            "original_device_class": None,
            "original_icon": None,
            "original_name": None,
            "platform": "test_platform",
            "translation_key": None,
            "unique_id": "1234",
        },
    }