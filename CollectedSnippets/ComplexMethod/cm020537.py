async def test_enter_and_exit(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    gpslogger_client: TestClient,
    webhook_id: str,
) -> None:
    """Test when there is a known zone."""
    url = f"/api/webhook/{webhook_id}"

    data = {"latitude": HOME_LATITUDE, "longitude": HOME_LONGITUDE, "device": "123"}

    # Enter the Home
    req = await gpslogger_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == STATE_HOME

    # Enter Home again
    req = await gpslogger_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == STATE_HOME

    data["longitude"] = 0
    data["latitude"] = 0

    # Enter Somewhere else
    req = await gpslogger_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['device']}").state
    assert state_name == STATE_NOT_HOME

    assert len(device_registry.devices) == 1
    assert len(entity_registry.entities) == 1