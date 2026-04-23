async def test_load_categories(
    hass: HomeAssistant, category_registry: cr.CategoryRegistry
) -> None:
    """Make sure that we can load/save data correctly."""
    category1 = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category2 = category_registry.async_create(
        scope="automation",
        name="Something else",
        icon="mdi:leaf",
    )
    category3 = category_registry.async_create(
        scope="zone",
        name="Grocery stores",
        icon="mdi:store",
    )

    assert len(category_registry.categories) == 2
    assert len(category_registry.categories["automation"]) == 2
    assert len(category_registry.categories["zone"]) == 1

    registry2 = cr.CategoryRegistry(hass)
    await flush_store(category_registry._store)
    await registry2.async_load()

    assert len(registry2.categories) == 2
    assert len(registry2.categories["automation"]) == 2
    assert len(registry2.categories["zone"]) == 1
    assert list(category_registry.categories) == list(registry2.categories)
    assert list(category_registry.categories["automation"]) == list(
        registry2.categories["automation"]
    )
    assert list(category_registry.categories["zone"]) == list(
        registry2.categories["zone"]
    )

    category1_registry2 = registry2.async_get_category(
        scope="automation", category_id=category1.category_id
    )
    assert category1_registry2.category_id == category1.category_id
    assert category1_registry2.name == category1.name
    assert category1_registry2.icon == category1.icon

    category2_registry2 = registry2.async_get_category(
        scope="automation", category_id=category2.category_id
    )
    assert category2_registry2.category_id == category2.category_id
    assert category2_registry2.name == category2.name
    assert category2_registry2.icon == category2.icon

    category3_registry2 = registry2.async_get_category(
        scope="zone", category_id=category3.category_id
    )
    assert category3_registry2.category_id == category3.category_id
    assert category3_registry2.name == category3.name
    assert category3_registry2.icon == category3.icon