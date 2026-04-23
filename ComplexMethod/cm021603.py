async def test_ws_update(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, storage_setup
) -> None:
    """Test updating via WS."""
    manager = hass.data[DOMAIN][1]

    client = await hass_ws_client(hass)
    persons = manager.async_items()

    resp = await client.send_json(
        {
            "id": 6,
            "type": "person/update",
            "person_id": persons[0]["id"],
            "user_id": persons[0]["user_id"],
        }
    )
    resp = await client.receive_json()

    assert resp["success"]

    resp = await client.send_json(
        {
            "id": 7,
            "type": "person/update",
            "person_id": persons[0]["id"],
            "name": "Updated Name",
            "device_trackers": [DEVICE_TRACKER_2],
            "user_id": None,
            "picture": "/bla",
        }
    )
    resp = await client.receive_json()

    persons = manager.async_items()
    assert len(persons) == 1

    assert resp["success"]
    assert resp["result"] == persons[0]
    assert persons[0]["name"] == "Updated Name"
    assert persons[0]["name"] == "Updated Name"
    assert persons[0]["device_trackers"] == [DEVICE_TRACKER_2]
    assert persons[0]["user_id"] is None
    assert persons[0]["picture"] == "/bla"

    state = hass.states.get("person.tracked_person")
    assert state.name == "Updated Name"