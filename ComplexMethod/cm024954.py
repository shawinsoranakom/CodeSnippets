def test_migrate_entity_to_new_platform(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    create_kwargs: dict,
    migrate_kwargs: dict,
    new_subentry_id: str | None,
) -> None:
    """Test migrate_entity_to_new_platform."""
    orig_config_entry = MockConfigEntry(
        domain="light",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-1",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    orig_config_entry.add_to_hass(hass)
    orig_unique_id = "5678"

    orig_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        orig_unique_id,
        suggested_object_id="light",
        config_entry=orig_config_entry,
        disabled_by=er.RegistryEntryDisabler.USER,
        entity_category=EntityCategory.CONFIG,
        original_device_class="mock-device-class",
        original_icon="initial-original_icon",
        original_name="initial-original_name",
        **create_kwargs,
    )
    assert entity_registry.async_get("light.light") is orig_entry
    entity_registry.async_update_entity(
        "light.light",
        name="new_name",
        icon="new_icon",
    )

    new_config_entry = MockConfigEntry(
        domain="light",
        subentries_data=[
            config_entries.ConfigSubentryData(
                data={},
                subentry_id="mock-subentry-id-2",
                subentry_type="test",
                title="Mock title",
                unique_id="test",
            ),
        ],
    )
    new_config_entry.add_to_hass(hass)
    new_unique_id = "1234"

    assert entity_registry.async_update_entity_platform(
        "light.light",
        "hue2",
        new_unique_id=new_unique_id,
        new_config_entry_id=new_config_entry.entry_id,
        **migrate_kwargs,
    )

    assert not entity_registry.async_get_entity_id("light", "hue", orig_unique_id)

    assert (new_entry := entity_registry.async_get("light.light")) is not orig_entry

    assert new_entry.config_entry_id == new_config_entry.entry_id
    assert new_entry.config_subentry_id == new_subentry_id
    assert new_entry.unique_id == new_unique_id
    assert new_entry.name == "new_name"
    assert new_entry.icon == "new_icon"
    assert new_entry.platform == "hue2"

    # Test nonexisting entity
    with pytest.raises(KeyError):
        entity_registry.async_update_entity_platform(
            "light.not_a_real_light",
            "hue2",
            new_unique_id=new_unique_id,
            new_config_entry_id=new_config_entry.entry_id,
        )

    # Test migrate entity without new config entry ID
    with pytest.raises(ValueError):
        entity_registry.async_update_entity_platform(
            "light.light",
            "hue3",
        )

    # Test entity with a state
    hass.states.async_set("light.light", "on")
    with pytest.raises(ValueError):
        entity_registry.async_update_entity_platform(
            "light.light",
            "hue2",
            new_unique_id=new_unique_id,
            new_config_entry_id=new_config_entry.entry_id,
        )