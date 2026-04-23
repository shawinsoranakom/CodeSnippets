async def test_storage_collection_websocket_subscribe(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test exposing a storage collection via websockets."""
    store = storage.Store(hass, 1, "test-data")
    coll = MockStorageCollection(store)
    changes = track_changes(coll)
    collection.DictStorageCollectionWebsocket(
        coll,
        "test_item/collection",
        "test_item",
        {vol.Required("name"): str, vol.Required("immutable_string"): str},
        {vol.Optional("name"): str},
    ).async_setup(hass)

    client = await hass_ws_client(hass)

    # Subscribe
    await client.send_json_auto_id({"type": "test_item/collection/subscribe"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None
    assert len(changes) == 0
    event_id = response["id"]

    response = await client.receive_json()
    assert response["id"] == event_id
    assert response["event"] == []

    # Create invalid
    await client.send_json_auto_id(
        {
            "type": "test_item/collection/create",
            "name": 1,
            # Forgot to add immutable_string
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "invalid_format"
    assert len(changes) == 0

    # Create
    await client.send_json_auto_id(
        {
            "type": "test_item/collection/create",
            "name": "Initial Name",
            "immutable_string": "no-changes",
        }
    )
    response = await client.receive_json()
    assert response["id"] == event_id
    assert response["event"] == [
        {
            "change_type": "added",
            "item": {
                "id": "initial_name",
                "immutable_string": "no-changes",
                "name": "Initial Name",
            },
            "test_item_id": "initial_name",
        }
    ]
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "id": "initial_name",
        "name": "Initial Name",
        "immutable_string": "no-changes",
    }
    assert len(changes) == 1
    assert changes[0] == (collection.CHANGE_ADDED, "initial_name", response["result"])

    # Subscribe again
    await client.send_json_auto_id({"type": "test_item/collection/subscribe"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] is None
    event_id_2 = response["id"]

    response = await client.receive_json()
    assert response["id"] == event_id_2
    assert response["event"] == [
        {
            "change_type": "added",
            "item": {
                "id": "initial_name",
                "immutable_string": "no-changes",
                "name": "Initial Name",
            },
            "test_item_id": "initial_name",
        },
    ]

    await client.send_json_auto_id(
        {"type": "unsubscribe_events", "subscription": event_id_2}
    )
    response = await client.receive_json()
    assert response["success"]

    # List
    await client.send_json_auto_id({"type": "test_item/collection/list"})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == [
        {
            "id": "initial_name",
            "name": "Initial Name",
            "immutable_string": "no-changes",
        }
    ]
    assert len(changes) == 1

    # Update invalid data
    await client.send_json_auto_id(
        {
            "type": "test_item/collection/update",
            "test_item_id": "initial_name",
            "immutable_string": "no-changes",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "invalid_format"
    assert len(changes) == 1

    # Update invalid item
    await client.send_json_auto_id(
        {
            "type": "test_item/collection/update",
            "test_item_id": "non-existing",
            "name": "Updated name",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "not_found"
    assert len(changes) == 1

    # Update
    await client.send_json_auto_id(
        {
            "type": "test_item/collection/update",
            "test_item_id": "initial_name",
            "name": "Updated name",
        }
    )
    response = await client.receive_json()
    assert response["id"] == event_id
    assert response["event"] == [
        {
            "change_type": "updated",
            "item": {
                "id": "initial_name",
                "immutable_string": "no-changes",
                "name": "Updated name",
            },
            "test_item_id": "initial_name",
        }
    ]
    response = await client.receive_json()
    assert response["success"]
    assert response["result"] == {
        "id": "initial_name",
        "name": "Updated name",
        "immutable_string": "no-changes",
    }
    assert len(changes) == 2
    assert changes[1] == (collection.CHANGE_UPDATED, "initial_name", response["result"])

    # Delete invalid ID
    await client.send_json_auto_id(
        {"type": "test_item/collection/update", "test_item_id": "non-existing"}
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "not_found"
    assert len(changes) == 2

    # Delete
    await client.send_json_auto_id(
        {"type": "test_item/collection/delete", "test_item_id": "initial_name"}
    )
    response = await client.receive_json()
    assert response["id"] == event_id
    assert response["event"] == [
        {
            "change_type": "removed",
            "item": {
                "id": "initial_name",
                "immutable_string": "no-changes",
                "name": "Updated name",
            },
            "test_item_id": "initial_name",
        }
    ]
    response = await client.receive_json()
    assert response["success"]

    assert len(changes) == 3
    assert changes[2] == (
        collection.CHANGE_REMOVED,
        "initial_name",
        {
            "id": "initial_name",
            "immutable_string": "no-changes",
            "name": "Updated name",
        },
    )