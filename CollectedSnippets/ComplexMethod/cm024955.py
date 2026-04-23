async def test_restore_entity(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Make sure entity registry id is stable and user configurations are restored."""
    update_events = async_capture_events(hass, er.EVENT_ENTITY_REGISTRY_UPDATED)
    config_entry = MockConfigEntry(
        domain="light",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1-2",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    config_entry.add_to_hass(hass)
    device_entry_1 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    device_entry_2 = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "22:34:56:AB:CD:EF")},
    )
    entry1 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        capabilities={"key1": "value1"},
        config_entry=config_entry,
        config_subentry_id="mock-subentry-id-1-1",
        device_id=device_entry_1.id,
        disabled_by=er.RegistryEntryDisabler.DEVICE,
        entity_category=EntityCategory.DIAGNOSTIC,
        get_initial_options=lambda: {"test_domain": {"key1": "value1"}},
        has_entity_name=True,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
        object_id_base="original_name_1",
        original_device_class="device_class_1",
        original_icon="original_icon_1",
        original_name="original_name_1",
        suggested_object_id="suggested_1",
        supported_features=1,
        translation_key="translation_key_1",
        unit_of_measurement="unit_1",
    )
    entry2 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        config_subentry_id="mock-subentry-id-1-1",
    )
    entry3 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "abcd",
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )

    # Apply user customizations
    entry1 = entity_registry.async_update_entity(
        entry1.entity_id,
        aliases=["alias1", "alias2"],
        area_id="12345A",
        categories={"scope1": "id", "scope2": "id"},
        device_class="device_class_user",
        disabled_by=er.RegistryEntryDisabler.USER,
        hidden_by=er.RegistryEntryHider.USER,
        icon="icon_user",
        labels={"label1", "label2"},
        name="Test Friendly Name",
        new_entity_id="light.custom_1",
    )
    entry1 = entity_registry.async_update_entity_options(
        entry1.entity_id, "options_domain", {"key": "value"}
    )

    entity_registry.async_remove(entry1.entity_id)
    entity_registry.async_remove(entry2.entity_id)
    entity_registry.async_remove(entry3.entity_id)
    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 3

    # Re-add entities, integration has changed
    entry1_restored = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        capabilities={"key2": "value2"},
        config_entry=config_entry,
        config_subentry_id="mock-subentry-id-1-2",
        device_id=device_entry_2.id,
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        entity_category=EntityCategory.CONFIG,
        get_initial_options=lambda: {"test_domain": {"key2": "value2"}},
        has_entity_name=False,
        hidden_by=None,
        object_id_base="original_name_2",
        original_device_class="device_class_2",
        original_icon="original_icon_2",
        original_name="original_name_2",
        suggested_object_id="suggested_2",
        supported_features=2,
        translation_key="translation_key_2",
        unit_of_measurement="unit_2",
    )
    # Add back the second entity without config entry and with different
    # disabled_by and hidden_by settings
    entry2_restored = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
    )
    # Add back the third entity with different disabled_by and hidden_by settings
    entry3_restored = entity_registry.async_get_or_create("light", "hue", "abcd")

    assert len(entity_registry.entities) == 3
    assert len(entity_registry.deleted_entities) == 0
    assert entry1 != entry1_restored
    # entity_id and user customizations are restored. new integration options are
    # respected.
    assert entry1_restored == er.RegistryEntry(
        entity_id="light.custom_1",
        unique_id="1234",
        platform="hue",
        aliases=["alias1", "alias2"],
        area_id="12345A",
        categories={"scope1": "id", "scope2": "id"},
        capabilities={"key2": "value2"},
        config_entry_id=config_entry.entry_id,
        config_subentry_id="mock-subentry-id-1-2",
        created_at=utcnow(),
        device_class="device_class_user",
        device_id=device_entry_2.id,
        disabled_by=er.RegistryEntryDisabler.USER,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=False,
        hidden_by=er.RegistryEntryHider.USER,
        icon="icon_user",
        id=entry1.id,
        labels={"label1", "label2"},
        modified_at=utcnow(),
        name="Test Friendly Name",
        object_id_base="original_name_2",
        options={"options_domain": {"key": "value"}, "test_domain": {"key1": "value1"}},
        original_device_class="device_class_2",
        original_icon="original_icon_2",
        original_name="original_name_2",
        suggested_object_id="suggested_2",
        supported_features=2,
        translation_key="translation_key_2",
        unit_of_measurement="unit_2",
    )
    assert entry2 != entry2_restored
    # Config entry and subentry are not restored
    assert (
        attr.evolve(
            entry2,
            config_entry_id=None,
            config_subentry_id=None,
            disabled_by=None,
            hidden_by=None,
        )
        == entry2_restored
    )
    assert entry3 == entry3_restored

    # Remove two of the entities again, then bump time
    entity_registry.async_remove(entry1_restored.entity_id)
    entity_registry.async_remove(entry2.entity_id)
    assert len(entity_registry.entities) == 1
    assert len(entity_registry.deleted_entities) == 2
    freezer.tick(timedelta(seconds=er.ORPHANED_ENTITY_KEEP_SECONDS + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Re-add two entities, expect to get a new id after the purge for entity w/o config entry
    entry1_restored = entity_registry.async_get_or_create(
        "light", "hue", "1234", config_entry=config_entry
    )
    entry2_restored = entity_registry.async_get_or_create("light", "hue", "5678")
    assert len(entity_registry.entities) == 3
    assert len(entity_registry.deleted_entities) == 0
    assert entry1.id == entry1_restored.id
    assert entry2.id != entry2_restored.id

    # Remove the first entity, then its config entry, finally bump time
    entity_registry.async_remove(entry1_restored.entity_id)
    assert len(entity_registry.entities) == 2
    assert len(entity_registry.deleted_entities) == 1
    entity_registry.async_clear_config_entry(config_entry.entry_id)
    freezer.tick(timedelta(seconds=er.ORPHANED_ENTITY_KEEP_SECONDS + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Re-add the entity, expect to get a new id after the purge
    entry1_restored = entity_registry.async_get_or_create(
        "light", "hue", "1234", config_entry=config_entry
    )
    assert len(entity_registry.entities) == 3
    assert len(entity_registry.deleted_entities) == 0
    assert entry1.id != entry1_restored.id

    # Check the events
    await hass.async_block_till_done()
    assert len(update_events) == 17
    assert update_events[0].data == {
        "action": "create",
        "entity_id": "light.suggested_1",
    }
    assert update_events[1].data == {"action": "create", "entity_id": "light.hue_5678"}
    assert update_events[2].data == {"action": "create", "entity_id": "light.hue_abcd"}
    assert update_events[3].data["action"] == "update"
    assert update_events[4].data["action"] == "update"
    assert update_events[5].data == {"action": "remove", "entity_id": "light.custom_1"}
    assert update_events[6].data == {"action": "remove", "entity_id": "light.hue_5678"}
    assert update_events[7].data == {"action": "remove", "entity_id": "light.hue_abcd"}
    # Restore entities the 1st time
    assert update_events[8].data == {"action": "create", "entity_id": "light.custom_1"}
    assert update_events[9].data == {"action": "create", "entity_id": "light.hue_5678"}
    assert update_events[10].data == {"action": "create", "entity_id": "light.hue_abcd"}
    assert update_events[11].data == {"action": "remove", "entity_id": "light.custom_1"}
    assert update_events[12].data == {"action": "remove", "entity_id": "light.hue_5678"}
    # Restore entities the 2nd time
    assert update_events[13].data == {"action": "create", "entity_id": "light.custom_1"}
    assert update_events[14].data == {"action": "create", "entity_id": "light.hue_5678"}
    assert update_events[15].data == {"action": "remove", "entity_id": "light.custom_1"}
    # Restore entities the 3rd time
    assert update_events[16].data == {"action": "create", "entity_id": "light.hue_1234"}