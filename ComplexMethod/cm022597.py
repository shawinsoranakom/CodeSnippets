async def test_enter_and_exit(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client,
    webhook_id,
) -> None:
    """Test when there is a known zone."""
    url = f"/api/webhook/{webhook_id}"
    data = {"lat": str(HOME_LATITUDE), "lon": str(HOME_LONGITUDE), "id": "123"}

    # Enter the Home
    req = await client.post(url, params=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['id']}").state
    assert state_name == STATE_HOME

    # Enter Home again
    req = await client.post(url, params=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['id']}").state
    assert state_name == STATE_HOME

    data["lon"] = 0
    data["lat"] = 0

    # Enter Somewhere else
    req = await client.post(url, params=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    state_name = hass.states.get(f"{DEVICE_TRACKER_DOMAIN}.{data['id']}").state
    assert state_name == STATE_NOT_HOME

    assert len(device_registry.devices) == 1

    assert len(entity_registry.entities) == 1