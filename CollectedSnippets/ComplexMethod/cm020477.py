async def snapshot_platform(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    snapshot: SnapshotAssertion,
    config_entry_id: str,
) -> None:
    """Snapshot a platform."""
    device_entries = dr.async_entries_for_config_entry(device_registry, config_entry_id)
    assert device_entries
    for device_entry in device_entries:
        assert device_entry == snapshot(name=f"{device_entry.name}-entry"), (
            f"device entry snapshot failed for {device_entry.name}"
        )

    entity_entries = er.async_entries_for_config_entry(entity_registry, config_entry_id)
    assert entity_entries
    assert len({entity_entry.domain for entity_entry in entity_entries}) == 1, (
        "Please limit the loaded platforms to 1 platform."
    )

    translations = await async_get_translations(hass, "en", "entity", [DOMAIN])
    unique_device_classes = []
    for entity_entry in entity_entries:
        if entity_entry.translation_key:
            key = f"component.{DOMAIN}.entity.{entity_entry.domain}.{entity_entry.translation_key}.name"
            single_device_class_translation = False
            if key not in translations:  # No name translation
                if entity_entry.original_device_class not in unique_device_classes:
                    single_device_class_translation = True
                    unique_device_classes.append(entity_entry.original_device_class)
            assert (key in translations) or single_device_class_translation, (
                f"No translation or non unique device_class for entity {entity_entry.unique_id}, expected {key}"
            )
        assert entity_entry == snapshot(name=f"{entity_entry.entity_id}-entry"), (
            f"entity entry snapshot failed for {entity_entry.entity_id}"
        )
        if entity_entry.disabled_by is None:
            state = hass.states.get(entity_entry.entity_id)
            assert state, f"State not found for {entity_entry.entity_id}"
            assert state == snapshot(name=f"{entity_entry.entity_id}-state"), (
                f"state snapshot failed for {entity_entry.entity_id}"
            )