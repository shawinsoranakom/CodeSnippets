async def test_loading_saving_data(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that we load/save data correctly."""
    mock_config = MockConfigEntry(domain="light")
    mock_config.add_to_hass(hass)

    device_entry = device_registry.async_get_or_create(
        config_entry_id=mock_config.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    orig_entry1 = entity_registry.async_get_or_create("light", "hue", "1234")
    orig_entry2 = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        capabilities={"max": 100},
        config_entry=mock_config,
        device_id=device_entry.id,
        disabled_by=er.RegistryEntryDisabler.HASS,
        entity_category=EntityCategory.CONFIG,
        hidden_by=er.RegistryEntryHider.INTEGRATION,
        has_entity_name=True,
        original_device_class="mock-device-class",
        original_icon="hass:original-icon",
        original_name="Original Name",
        supported_features=5,
        translation_key="initial-translation_key",
        unit_of_measurement="initial-unit_of_measurement",
    )
    entity_registry.async_update_entity(
        orig_entry2.entity_id,
        aliases=["initial_alias_1", "initial_alias_2"],
        area_id="mock-area-id",
        device_class="user-class",
        name="User Name",
        icon="hass:user-icon",
    )
    entity_registry.async_update_entity_options(
        orig_entry2.entity_id, "light", {"minimum_brightness": 20}
    )
    entity_registry.async_update_entity(
        orig_entry2.entity_id,
        categories={"scope", "id"},
        labels={"label1", "label2"},
    )
    orig_entry2 = entity_registry.async_get(orig_entry2.entity_id)
    orig_entry3 = entity_registry.async_get_or_create("light", "hue", "ABCD")
    orig_entry4 = entity_registry.async_get_or_create("light", "hue", "EFGH")
    entity_registry.async_remove(orig_entry3.entity_id)
    entity_registry.async_remove(orig_entry4.entity_id)

    assert len(entity_registry.entities) == 2
    assert len(entity_registry.deleted_entities) == 2

    # Now load written data in new registry
    registry2 = er.EntityRegistry(hass)
    await flush_store(entity_registry._store)
    await registry2.async_load()

    # Ensure same order
    assert list(entity_registry.entities) == list(registry2.entities)
    assert list(entity_registry.deleted_entities) == list(registry2.deleted_entities)
    new_entry1 = entity_registry.async_get_or_create("light", "hue", "1234")
    new_entry2 = entity_registry.async_get_or_create("light", "hue", "5678")
    new_entry3 = entity_registry.async_get_or_create("light", "hue", "ABCD")
    new_entry4 = entity_registry.async_get_or_create("light", "hue", "EFGH")

    assert orig_entry1 == new_entry1
    assert orig_entry2 == new_entry2

    # By converting a deleted device to a active device, the modified_at will be updated
    assert orig_entry3.modified_at < new_entry3.modified_at
    assert attr.evolve(orig_entry3, modified_at=new_entry3.modified_at) == new_entry3
    assert orig_entry4.modified_at < new_entry4.modified_at
    assert attr.evolve(orig_entry4, modified_at=new_entry4.modified_at) == new_entry4

    assert new_entry2.area_id == "mock-area-id"
    assert new_entry2.categories == {"scope", "id"}
    assert new_entry2.capabilities == {"max": 100}
    assert new_entry2.config_entry_id == mock_config.entry_id
    assert new_entry2.device_class == "user-class"
    assert new_entry2.device_id == device_entry.id
    assert new_entry2.disabled_by is er.RegistryEntryDisabler.HASS
    assert new_entry2.entity_category == "config"
    assert new_entry2.icon == "hass:user-icon"
    assert new_entry2.hidden_by == er.RegistryEntryHider.INTEGRATION
    assert new_entry2.has_entity_name is True
    assert new_entry2.labels == {"label1", "label2"}
    assert new_entry2.name == "User Name"
    assert new_entry2.options == {"light": {"minimum_brightness": 20}}
    assert new_entry2.original_device_class == "mock-device-class"
    assert new_entry2.original_icon == "hass:original-icon"
    assert new_entry2.original_name == "Original Name"
    assert new_entry2.supported_features == 5
    assert new_entry2.translation_key == "initial-translation_key"
    assert new_entry2.unit_of_measurement == "initial-unit_of_measurement"