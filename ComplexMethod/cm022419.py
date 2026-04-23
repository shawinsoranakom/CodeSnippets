async def test_update_floor(
    client: MockHAClientWebSocket,
    floor_registry: fr.FloorRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update entry."""
    created_at = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_at)
    floor = floor_registry.async_create("First floor")
    assert len(floor_registry.floors) == 1
    modified_at = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "Second floor",
            "aliases": ["top floor", "attic"],
            "icon": "mdi:home-floor-2",
            "type": "config/floor_registry/update",
            "level": 2,
        }
    )

    msg = await client.receive_json()

    assert len(floor_registry.floors) == 1
    assert msg["result"] == {
        "aliases": unordered(["top floor", "attic"]),
        "created_at": created_at.timestamp(),
        "icon": "mdi:home-floor-2",
        "floor_id": floor.floor_id,
        "modified_at": modified_at.timestamp(),
        "name": "Second floor",
        "level": 2,
    }

    modified_at = datetime.fromisoformat("2024-07-16T13:50:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": [],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(floor_registry.floors) == 1
    assert msg["result"] == {
        "aliases": [],
        "created_at": created_at.timestamp(),
        "icon": None,
        "floor_id": floor.floor_id,
        "modified_at": modified_at.timestamp(),
        "name": "First floor",
        "level": None,
    }

    # Add invalid aliases
    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": ["top floor", "attic", "", " "],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(floor_registry.floors) == 1
    assert msg["result"] == {
        "aliases": unordered(["top floor", "attic"]),
        "created_at": created_at.timestamp(),
        "icon": None,
        "floor_id": floor.floor_id,
        "modified_at": modified_at.timestamp(),
        "name": "First floor",
        "level": None,
    }

    # Add alias with trailing and leading whitespaces
    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)
    await client.send_json_auto_id(
        {
            "floor_id": floor.floor_id,
            "name": "First floor",
            "aliases": ["top floor", "attic", "solaio "],
            "icon": None,
            "level": None,
            "type": "config/floor_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(floor_registry.floors) == 1
    assert msg["result"] == {
        "aliases": unordered(["top floor", "attic", "solaio"]),
        "created_at": created_at.timestamp(),
        "icon": None,
        "floor_id": floor.floor_id,
        "modified_at": modified_at.timestamp(),
        "name": "First floor",
        "level": None,
    }