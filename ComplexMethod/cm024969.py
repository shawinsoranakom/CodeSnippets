async def test_create_category(
    hass: HomeAssistant, category_registry: cr.CategoryRegistry
) -> None:
    """Make sure that we can create new categories."""
    update_events = async_capture_events(hass, cr.EVENT_CATEGORY_REGISTRY_UPDATED)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )

    assert category.category_id
    assert category.name == "Energy saving"
    assert category.icon == "mdi:leaf"

    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    await hass.async_block_till_done()

    assert len(update_events) == 1
    assert update_events[0].data == {
        "action": "create",
        "scope": "automation",
        "category_id": category.category_id,
    }