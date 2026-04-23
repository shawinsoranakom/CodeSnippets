async def test_removing_labels_deleted_entity(
    entity_registry: er.EntityRegistry,
) -> None:
    """Make sure we can clear labels."""
    entry1 = entity_registry.async_get_or_create(
        domain="light", platform="hue", unique_id="5678"
    )
    entry1 = entity_registry.async_update_entity(
        entry1.entity_id, labels={"label1", "label2"}
    )
    entry2 = entity_registry.async_get_or_create(
        domain="light", platform="hue", unique_id="1234"
    )
    entry2 = entity_registry.async_update_entity(entry2.entity_id, labels={"label3"})

    entity_registry.async_remove(entry1.entity_id)
    entity_registry.async_remove(entry2.entity_id)
    entity_registry.async_clear_label_id("label1")
    entry1_cleared_label1 = entity_registry.async_get_or_create(
        domain="light", platform="hue", unique_id="5678"
    )

    entity_registry.async_remove(entry1.entity_id)
    entity_registry.async_clear_label_id("label2")
    entry1_cleared_label2 = entity_registry.async_get_or_create(
        domain="light", platform="hue", unique_id="5678"
    )
    entry2_restored = entity_registry.async_get_or_create(
        domain="light", platform="hue", unique_id="1234"
    )

    assert entry1_cleared_label1
    assert entry1_cleared_label2
    assert entry1 != entry1_cleared_label1
    assert entry1 != entry1_cleared_label2
    assert entry1_cleared_label1 != entry1_cleared_label2
    assert entry1.labels == {"label1", "label2"}
    assert entry1_cleared_label1.labels == {"label2"}
    assert not entry1_cleared_label2.labels
    assert entry2 != entry2_restored
    assert entry2_restored.labels == {"label3"}