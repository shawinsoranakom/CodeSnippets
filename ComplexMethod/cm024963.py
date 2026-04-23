async def test_removing_categories(entity_registry: er.EntityRegistry) -> None:
    """Make sure we can clear categories."""
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="5678",
    )
    entry = entity_registry.async_update_entity(
        entry.entity_id, categories={"scope1": "id", "scope2": "id"}
    )

    entity_registry.async_clear_category_id("scope1", "id")
    entry_cleared_scope1 = entity_registry.async_get(entry.entity_id)

    entity_registry.async_clear_category_id("scope2", "id")
    entry_cleared_scope2 = entity_registry.async_get(entry.entity_id)

    assert entry_cleared_scope1
    assert entry_cleared_scope2
    assert entry != entry_cleared_scope1
    assert entry != entry_cleared_scope2
    assert entry_cleared_scope1 != entry_cleared_scope2
    assert entry.categories == {"scope1": "id", "scope2": "id"}
    assert entry_cleared_scope1.categories == {"scope2": "id"}
    assert not entry_cleared_scope2.categories