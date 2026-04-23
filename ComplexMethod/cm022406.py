async def test_update_non_existing_category(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
) -> None:
    """Test update entry that should fail."""
    category = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": "idkfa",
            "name": "New category name",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "Category ID doesn't exist"
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    await client.send_json_auto_id(
        {
            "scope": "bullshizzle",
            "category_id": category.category_id,
            "name": "New category name",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "Category ID doesn't exist"
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1