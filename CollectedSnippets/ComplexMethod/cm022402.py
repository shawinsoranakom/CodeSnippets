async def test_create_category_with_name_already_in_use(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
) -> None:
    """Test create entry that should fail."""
    category_registry.async_create(
        scope="automation",
        name="Energy saving",
    )
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "name": "ENERGY SAVING",
            "type": "config/category_registry/create",
        }
    )

    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_info"
    assert msg["error"]["message"] == "The name 'ENERGY SAVING' is already in use"
    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1