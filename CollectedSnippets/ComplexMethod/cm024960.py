async def test_restore_entity_disabled_by_2(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    entity_disabled_by_initial: er.RegistryEntryDisabler | None,
    entity_disabled_by_restored: er.RegistryEntryDisabler | None,
) -> None:
    """Check how the disabled_by flag is treated when restoring an entity.

    In this test, the entity is restored without a config entry.
    """
    update_events = async_capture_events(hass, er.EVENT_ENTITY_REGISTRY_UPDATED)
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        capabilities={"key1": "value1"},
        config_entry=config_entry,
        config_subentry_id=None,
        device_id=device_entry.id,
        disabled_by=entity_disabled_by_initial,
        entity_category=EntityCategory.DIAGNOSTIC,
        get_initial_options=lambda: {"test_domain": {"key1": "value1"}},
        has_entity_name=True,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
        object_id_base="original_name_1",
        original_device_class="device_class_1",
        original_icon="original_icon_1",
        original_name="original_name_1",
        suggested_object_id="hue_5678",
        supported_features=1,
        translation_key="translation_key_1",
        unit_of_measurement="unit_1",
    )

    entity_registry.async_remove(entry.entity_id)
    assert len(entity_registry.entities) == 0
    assert len(entity_registry.deleted_entities) == 1

    # Re-add entity, integration has changed
    entry_restored = entity_registry.async_get_or_create(
        "light",
        "hue",
        "1234",
        capabilities={"key2": "value2"},
        config_entry=None,
        config_subentry_id=None,
        device_id=device_entry.id,
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

    assert len(entity_registry.entities) == 1
    assert len(entity_registry.deleted_entities) == 0
    assert entry != entry_restored
    # entity_id and user customizations are restored. new integration options are
    # respected.
    assert entry_restored == er.RegistryEntry(
        entity_id="light.hue_5678",
        unique_id="1234",
        platform="hue",
        aliases=[er.COMPUTED_NAME],
        area_id=None,
        categories={},
        capabilities={"key2": "value2"},
        config_entry_id=None,
        config_subentry_id=None,
        created_at=utcnow(),
        device_class=None,
        device_id=device_entry.id,
        disabled_by=entity_disabled_by_restored,
        entity_category=EntityCategory.CONFIG,
        has_entity_name=False,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
        icon=None,
        id=entry.id,
        labels=set(),
        modified_at=utcnow(),
        name=None,
        object_id_base="original_name_2",
        options={"test_domain": {"key1": "value1"}},
        original_device_class="device_class_2",
        original_icon="original_icon_2",
        original_name="original_name_2",
        suggested_object_id="suggested_2",
        supported_features=2,
        translation_key="translation_key_2",
        unit_of_measurement="unit_2",
    )

    # Check the events
    await hass.async_block_till_done()
    assert len(update_events) == 3
    assert update_events[0].data == {"action": "create", "entity_id": "light.hue_5678"}
    assert update_events[1].data == {"action": "remove", "entity_id": "light.hue_5678"}
    assert update_events[2].data == {"action": "create", "entity_id": "light.hue_5678"}