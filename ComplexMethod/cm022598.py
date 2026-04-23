async def test_enter_with_attrs_as_query(
    hass: HomeAssistant,
    client,
    webhook_id,
) -> None:
    """Test when additional attributes are present URL query."""
    url = f"/api/webhook/{webhook_id}"
    data = {
        "timestamp": 123456789,
        "lat": "1.0",
        "lon": "1.1",
        "id": "123",
        "accuracy": "10.5",
        "batt": 10,
        "speed": 100,
        "bearing": "105.32",
        "altitude": 102,
        "charge": "true",
    }

    req = await client.post(url, params=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['id']}")
    assert state.state == STATE_NOT_HOME
    assert state.attributes["gps_accuracy"] == 10.5
    assert state.attributes["battery_level"] == 10.0
    assert state.attributes["speed"] == 100.0
    assert state.attributes["bearing"] == 105.32
    assert state.attributes["altitude"] == 102.0
    assert "charge" not in state.attributes

    data = {
        "lat": str(HOME_LATITUDE),
        "lon": str(HOME_LONGITUDE),
        "id": "123",
        "accuracy": 123,
        "batt": 23,
        "speed": 23,
        "bearing": 123,
        "altitude": 123,
    }

    req = await client.post(url, params=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['id']}")
    assert state.state == STATE_HOME
    assert state.attributes["gps_accuracy"] == 123
    assert state.attributes["battery_level"] == 23
    assert state.attributes["speed"] == 23
    assert state.attributes["bearing"] == 123
    assert state.attributes["altitude"] == 123