async def test_labels_removed_from_entities(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test if label gets removed from entity when the label is removed."""
    label1 = label_registry.async_create("label1")
    label2 = label_registry.async_create("label2")
    assert len(label_registry.labels) == 2

    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="123",
    )
    entity_registry.async_update_entity(entry.entity_id, labels={label1.label_id})
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="456",
    )
    entity_registry.async_update_entity(entry.entity_id, labels={label2.label_id})
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="789",
    )
    entity_registry.async_update_entity(
        entry.entity_id, labels={label1.label_id, label2.label_id}
    )

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    assert len(entries) == 2
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    assert len(entries) == 2

    label_registry.async_delete(label1.label_id)
    await hass.async_block_till_done()

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    assert len(entries) == 0
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    assert len(entries) == 2

    label_registry.async_delete(label2.label_id)
    await hass.async_block_till_done()

    entries = er.async_entries_for_label(entity_registry, label1.label_id)
    assert len(entries) == 0
    entries = er.async_entries_for_label(entity_registry, label2.label_id)
    assert len(entries) == 0