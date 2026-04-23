async def test_create_area(
    client: MockHAClientWebSocket,
    area_registry: ar.AreaRegistry,
    freezer: FrozenDateTimeFactory,
    mock_temperature_humidity_entity: None,
) -> None:
    """Test create entry."""
    # Create area with only mandatory parameters
    await client.send_json_auto_id(
        {"name": "mock", "type": "config/area_registry/create"}
    )

    msg = await client.receive_json()

    assert msg["result"] == {
        "aliases": [],
        "area_id": ANY,
        "floor_id": None,
        "icon": None,
        "labels": [],
        "name": "mock",
        "picture": None,
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "temperature_entity_id": None,
        "humidity_entity_id": None,
    }
    assert len(area_registry.areas) == 1

    # Create area with all parameters
    await client.send_json_auto_id(
        {
            "aliases": ["alias_1", "alias_2"],
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": ["label_1", "label_2"],
            "name": "mock 2",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
            "type": "config/area_registry/create",
        }
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "aliases": unordered(["alias_1", "alias_2"]),
        "area_id": ANY,
        "floor_id": "first_floor",
        "icon": "mdi:garage",
        "labels": unordered(["label_1", "label_2"]),
        "name": "mock 2",
        "picture": "/image/example.png",
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "temperature_entity_id": "sensor.mock_temperature",
        "humidity_entity_id": "sensor.mock_humidity",
    }
    assert len(area_registry.areas) == 2

    # Create area with invalid aliases
    await client.send_json_auto_id(
        {
            "aliases": [" alias_1 ", "", " "],
            "floor_id": "first_floor",
            "icon": "mdi:garage",
            "labels": ["label_1", "label_2"],
            "name": "mock 3",
            "picture": "/image/example.png",
            "temperature_entity_id": "sensor.mock_temperature",
            "humidity_entity_id": "sensor.mock_humidity",
            "type": "config/area_registry/create",
        }
    )

    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] == {
        "aliases": unordered(["alias_1"]),
        "area_id": ANY,
        "floor_id": "first_floor",
        "icon": "mdi:garage",
        "labels": unordered(["label_1", "label_2"]),
        "name": "mock 3",
        "picture": "/image/example.png",
        "created_at": utcnow().timestamp(),
        "modified_at": utcnow().timestamp(),
        "temperature_entity_id": "sensor.mock_temperature",
        "humidity_entity_id": "sensor.mock_humidity",
    }
    assert len(area_registry.areas) == 3