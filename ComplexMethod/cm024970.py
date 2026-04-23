async def test_update_category(
    hass: HomeAssistant,
    category_registry: cr.CategoryRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Make sure that we can update categories."""
    created = datetime(2024, 2, 14, 12, 0, 0, tzinfo=UTC)
    freezer.move_to(created)
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )

    assert len(category_registry.categories["automation"]) == 1
    assert category == cr.CategoryEntry(
        category_id=category.category_id,
        created_at=created,
        modified_at=created,
        name="Energy saving",
        icon=None,
    )

    modified = datetime(2024, 3, 14, 12, 0, 0, tzinfo=UTC)
    freezer.move_to(modified)

    updated_category = category_registry.async_update(
        scope="automation",
        category_id=category.category_id,
        name="ENERGY SAVING",
        icon="mdi:leaf",
    )

    assert updated_category != category
    assert updated_category == cr.CategoryEntry(
        category_id=category.category_id,
        created_at=created,
        modified_at=modified,
        name="ENERGY SAVING",
        icon="mdi:leaf",
    )

    assert len(category_registry.categories["automation"]) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 2
    assert update_events[0].data == {
        "action": "create",
        "scope": "automation",
        "category_id": category.category_id,
    }
    assert update_events[1].data == {
        "action": "update",
        "scope": "automation",
        "category_id": category.category_id,
    }