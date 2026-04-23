async def test_beacon_enter_and_exit_car(
    hass: HomeAssistant, geofency_client: TestClient, webhook_id: str
) -> None:
    """Test use of mobile iBeacon."""
    url = f"/api/webhook/{webhook_id}"

    # Enter the Car away from Home zone
    req = await geofency_client.post(url, data=BEACON_ENTER_CAR)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(f"beacon_{BEACON_ENTER_CAR['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_NOT_HOME

    # Exit the Car away from Home zone
    req = await geofency_client.post(url, data=BEACON_EXIT_CAR)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(f"beacon_{BEACON_ENTER_CAR['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_NOT_HOME

    # Enter the Car in the Home zone
    data = BEACON_ENTER_CAR.copy()
    data["latitude"] = HOME_LATITUDE
    data["longitude"] = HOME_LONGITUDE
    req = await geofency_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(f"beacon_{data['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_HOME

    # Exit the Car in the Home zone
    req = await geofency_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(f"beacon_{data['name']}")
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_HOME