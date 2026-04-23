async def test_update_category(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update entry."""
    created = datetime(2024, 2, 14, 12, 0, 0)
    freezer.move_to(created)
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    modified = datetime(2024, 3, 14, 12, 0, 0)
    freezer.move_to(modified)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "ENERGY SAVING",
            "icon": "mdi:left",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1
    assert msg["result"] == {
        "icon": "mdi:left",
        "category_id": category.category_id,
        "created_at": created.timestamp(),
        "modified_at": modified.timestamp(),
        "name": "ENERGY SAVING",
    }

    modified = datetime(2024, 4, 14, 12, 0, 0)
    freezer.move_to(modified)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "Energy saving",
            "icon": None,
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1
    assert msg["result"] == {
        "icon": None,
        "category_id": category.category_id,
        "created_at": created.timestamp(),
        "modified_at": modified.timestamp(),
        "name": "Energy saving",
    }