async def test_update_label(
    client: MockHAClientWebSocket,
    label_registry: lr.LabelRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update entry."""
    created_at = datetime.fromisoformat("2024-07-16T13:30:00.900075+00:00")
    freezer.move_to(created_at)
    label = label_registry.async_create("mock")
    assert len(label_registry.labels) == 1

    modified_at = datetime.fromisoformat("2024-07-16T13:45:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "label_id": label.label_id,
            "name": "UPDATED",
            "icon": "mdi:test",
            "color": "#00FF00",
            "description": "This is a label description",
            "type": "config/label_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(label_registry.labels) == 1
    assert msg["result"] == {
        "color": "#00FF00",
        "created_at": created_at.timestamp(),
        "description": "This is a label description",
        "icon": "mdi:test",
        "label_id": "mock",
        "modified_at": modified_at.timestamp(),
        "name": "UPDATED",
    }

    modified_at = datetime.fromisoformat("2024-07-16T13:50:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "label_id": label.label_id,
            "name": "UPDATED AGAIN",
            "icon": None,
            "color": None,
            "description": None,
            "type": "config/label_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(label_registry.labels) == 1
    assert msg["result"] == {
        "color": None,
        "created_at": created_at.timestamp(),
        "description": None,
        "icon": None,
        "label_id": "mock",
        "modified_at": modified_at.timestamp(),
        "name": "UPDATED AGAIN",
    }

    modified_at = datetime.fromisoformat("2024-07-16T13:55:00.900075+00:00")
    freezer.move_to(modified_at)

    await client.send_json_auto_id(
        {
            "label_id": label.label_id,
            "name": "UPDATED YET AGAIN",
            "icon": None,
            "color": "primary",
            "description": None,
            "type": "config/label_registry/update",
        }
    )

    msg = await client.receive_json()

    assert len(label_registry.labels) == 1
    assert msg["result"] == {
        "color": "primary",
        "created_at": created_at.timestamp(),
        "description": None,
        "icon": None,
        "label_id": "mock",
        "modified_at": modified_at.timestamp(),
        "name": "UPDATED YET AGAIN",
    }