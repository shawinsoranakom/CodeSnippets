async def test_update_with_name_already_in_use(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
) -> None:
    """Test update entry."""
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    category = category_registry.async_create(
        scope="automation",
        name="Something else",
    )
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 2

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "category_id": category.category_id,
            "name": "ENERGY SAVING",
            "type": "config/category_registry/update",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "The name 'ENERGY SAVING' is already in use"
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 2