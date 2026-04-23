async def test_entries_for_category(entity_registry: er.EntityRegistry) -> None:
    """Test getting entity entries by category."""
    entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="000",
    )
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="123",
    )
    category_1 = entity_registry.async_update_entity(
        entry.entity_id, categories={"scope1": "id"}
    )
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="456",
    )
    category_2 = entity_registry.async_update_entity(
        entry.entity_id, categories={"scope2": "id"}
    )
    entry = entity_registry.async_get_or_create(
        domain="light",
        platform="hue",
        unique_id="789",
    )
    category_1_and_2 = entity_registry.async_update_entity(
        entry.entity_id, categories={"scope1": "id", "scope2": "id"}
    )

    entries = er.async_entries_for_category(entity_registry, "scope1", "id")
    assert len(entries) == 2
    assert entries == [category_1, category_1_and_2]

    entries = er.async_entries_for_category(entity_registry, "scope2", "id")
    assert len(entries) == 2
    assert entries == [category_2, category_1_and_2]

    assert not er.async_entries_for_category(entity_registry, "unknown", "id")
    assert not er.async_entries_for_category(entity_registry, "", "id")
    assert not er.async_entries_for_category(entity_registry, "scope1", "unknown")
    assert not er.async_entries_for_category(entity_registry, "scope1", "")