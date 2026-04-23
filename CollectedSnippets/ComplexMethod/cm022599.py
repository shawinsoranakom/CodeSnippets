async def test_enter_with_attrs_as_payload(
    hass: HomeAssistant, client, webhook_id
) -> None:
    """Test when additional attributes are present in JSON payload."""
    url = f"/api/webhook/{webhook_id}"
    data = {
        "location": {
            "coords": {
                "heading": "105.32",
                "latitude": "1.0",
                "longitude": "1.1",
                "accuracy": 10.5,
                "altitude": 102.0,
                "speed": 100.0,
            },
            "extras": {},
            "manual": True,
            "is_moving": False,
            "_": "&id=123&lat=1.0&lon=1.1&timestamp=2013-09-17T07:32:51Z&",
            "odometer": 0,
            "activity": {"type": "still"},
            "timestamp": "2013-09-17T07:32:51Z",
            "battery": {"level": 0.1, "is_charging": False},
        },
        "device_id": "123",
    }

    req = await client.post(url, json=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device_id']}")
    assert state.state == STATE_NOT_HOME
    assert state.attributes["gps_accuracy"] == 10.5
    assert state.attributes["battery_level"] == 10.0
    assert state.attributes["speed"] == 100.0
    assert state.attributes["bearing"] == 105.32
    assert state.attributes["altitude"] == 102.0