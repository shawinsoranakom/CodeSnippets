async def test_gps_enter_and_exit_home(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    geofency_client: TestClient,
    webhook_id: str,
) -> None:
    """Test GPS based zone enter and exit."""
    url = f"/api/webhook/{webhook_id}"

    # Enter the Home zone
    req = await geofency_client.post(url, data=GPS_ENTER_HOME)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(GPS_ENTER_HOME["device"])
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_HOME

    # Exit the Home zone
    req = await geofency_client.post(url, data=GPS_EXIT_HOME)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(GPS_EXIT_HOME["device"])
    state_name = hass.states.get(f"device_tracker.{device_name}").state
    assert state_name == STATE_NOT_HOME

    # Exit the Home zone with "Send Current Position" enabled
    data = GPS_EXIT_HOME.copy()
    data["currentLatitude"] = NOT_HOME_LATITUDE
    data["currentLongitude"] = NOT_HOME_LONGITUDE

    req = await geofency_client.post(url, data=data)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(GPS_EXIT_HOME["device"])
    current_latitude = hass.states.get(f"device_tracker.{device_name}").attributes[
        "latitude"
    ]
    assert current_latitude == NOT_HOME_LATITUDE
    current_longitude = hass.states.get(f"device_tracker.{device_name}").attributes[
        "longitude"
    ]
    assert current_longitude == NOT_HOME_LONGITUDE

    assert len(device_registry.devices) == 1
    assert len(entity_registry.entities) == 1