async def test_list_categories(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
) -> None:
    """Test list entries."""
    category1 = category_registry.async_create(
        scope="automation",
        name="Energy saving",
        icon="mdi:leaf",
    )
    category2 = category_registry.async_create(
        scope="automation",
        name="Something else",
        icon="mdi:home",
    )
    category3 = category_registry.async_create(
        scope="zone",
        name="Grocery stores",
        icon="mdi:store",
    )

    assert len(category_registry.categories) == 2
    assert len(category_registry.categories["automation"]) == 2
    assert len(category_registry.categories["zone"]) == 1

    await client.send_json_auto_id(
        {"type": "config/category_registry/list", "scope": "automation"}
    )

    msg = await client.receive_json()

    assert len(msg["result"]) == 2
    assert msg["result"][0] == {
        "category_id": category1.category_id,
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "name": "Energy saving",
        "icon": "mdi:leaf",
    }
    assert msg["result"][1] == {
        "category_id": category2.category_id,
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "name": "Something else",
        "icon": "mdi:home",
    }

    await client.send_json_auto_id(
        {"type": "config/category_registry/list", "scope": "zone"}
    )

    msg = await client.receive_json()

    assert len(msg["result"]) == 1
    assert msg["result"][0] == {
        "category_id": category3.category_id,
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "name": "Grocery stores",
        "icon": "mdi:store",
    }