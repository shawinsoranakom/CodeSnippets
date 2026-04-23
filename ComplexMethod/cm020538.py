async def test_enter_with_attrs(
    hass: HomeAssistant, gpslogger_client: TestClient, webhook_id: str
) -> None:
    """Test when additional attributes are present."""
    url = f"/api/webhook/{webhook_id}"

    data = {
        "latitude": 1.0,
        "longitude": 1.1,
        "device": "123",
        "accuracy": 10.5,
        "battery": 10,
        "speed": 100,
        "direction": 105.32,
        "altitude": 102,
        "provider": "gps",
        "activity": "running",
    }

    req = await gpslogger_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    assert state.state == STATE_NOT_HOME
    assert state.attributes["gps_accuracy"] == 10.5
    assert state.attributes["battery_level"] == 10.0
    assert state.attributes["speed"] == 100.0
    assert state.attributes["direction"] == 105.32
    assert state.attributes["altitude"] == 102.0
    assert state.attributes["provider"] == "gps"
    assert state.attributes["activity"] == "running"

    data = {
        "latitude": HOME_LATITUDE,
        "longitude": HOME_LONGITUDE,
        "device": "123",
        "accuracy": 123,
        "battery": 23,
        "speed": 23,
        "direction": 123,
        "altitude": 123,
        "provider": "gps",
        "activity": "idle",
    }

    req = await gpslogger_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}")
    assert state.state == STATE_HOME
    assert state.attributes["gps_accuracy"] == 123
    assert state.attributes["battery_level"] == 23
    assert state.attributes["speed"] == 23
    assert state.attributes["direction"] == 123
    assert state.attributes["altitude"] == 123
    assert state.attributes["provider"] == "gps"
    assert state.attributes["activity"] == "idle"