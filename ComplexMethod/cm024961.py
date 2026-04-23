async def test_removing_labels(entity_registry: er.EntityRegistry) -> None:
    """Make sure we can clear labels."""
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="5678",
    )
    entry = entity_registry.async_update_entity(
        entry.entity_id, labels={"label1", "label2"}
    )

    entity_registry.async_clear_label_id("label1")
    entry_cleared_label1 = entity_registry.async_get(entry.entity_id)

    entity_registry.async_clear_label_id("label2")
    entry_cleared_label2 = entity_registry.async_get(entry.entity_id)

    assert entry_cleared_label1
    assert entry_cleared_label2
    assert entry != entry_cleared_label1
    assert entry != entry_cleared_label2
    assert entry_cleared_label1 != entry_cleared_label2
    assert entry.labels == {"label1", "label2"}
    assert entry_cleared_label1.labels == {"label2"}
    assert not entry_cleared_label2.labels