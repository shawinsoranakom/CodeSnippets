async def test_create_category(
    client: MockHAClientWebSocket,
    category_registry: cr.CategoryRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test create entry."""
    created1 = datetime(2024, 2, 14, 12, 0, 0)
    freezer.move_to(created1)
    await client.send_json_auto_id(
        {
            "type": "config/category_registry/create",
            "scope": "automation",
            "name": "Energy saving",
            "icon": "mdi:leaf",
        }
    )

    msg = await client.receive_json()

    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 1

    assert msg["result"] == {
        "icon": "mdi:leaf",
        "category_id": ANY,
        "created_at": created1.timestamp(),
        "modified_at": created1.timestamp(),
        "name": "Energy saving",
    }

    created2 = datetime(2024, 3, 14, 12, 0, 0)
    freezer.move_to(created2)

    await client.send_json_auto_id(
        {
            "scope": "automation",
            "name": "Something else",
            "type": "config/category_registry/create",
        }
    )

    msg = await client.receive_json()

    assert len(category_registry.categories) == 1
    assert len(category_registry.categories["automation"]) == 2

    assert msg["result"] == {
        "icon": None,
        "category_id": ANY,
        "created_at": created2.timestamp(),
        "modified_at": created2.timestamp(),
        "name": "Something else",
    }

    created3 = datetime(2024, 4, 14, 12, 0, 0)
    freezer.move_to(created3)

    # Test adding the same one again in a different scope
    await client.send_json_auto_id(
        {
            "type": "config/category_registry/create",
            "scope": "script",
            "name": "Energy saving",
            "icon": "mdi:leaf",
        }
    )

    msg = await client.receive_json()

    assert len(category_registry.categories) == 2
    assert len(category_registry.categories["automation"]) == 2
    assert len(category_registry.categories["script"]) == 1

    assert msg["result"] == {
        "icon": "mdi:leaf",
        "category_id": ANY,
        "created_at": created3.timestamp(),
        "modified_at": created3.timestamp(),
        "name": "Energy saving",
    }