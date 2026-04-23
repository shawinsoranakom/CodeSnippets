async def test_load_unload_entry(
    hass: HomeAssistant, geofency_client: TestClient, webhook_id: str
) -> None:
    """Test that the appropriate dispatch signals are added and removed."""
    url = f"/api/webhook/{webhook_id}"

    # Enter the Home zone
    req = await geofency_client.post(url, data=GPS_ENTER_HOME)
    await hass.async_block_till_done()
    assert req.status == HTTPStatus.OK
    device_name = slugify(GPS_ENTER_HOME["device"])
    state_1 = hass.states.get(f"device_tracker.{device_name}")
    assert state_1.state == STATE_HOME

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert len(entry.runtime_data) == 1

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state_2 = hass.states.get(f"device_tracker.{device_name}")
    assert state_2 is not None
    assert state_1 is not state_2

    assert state_2.state == STATE_HOME
    assert state_2.attributes[ATTR_LATITUDE] == HOME_LATITUDE
    assert state_2.attributes[ATTR_LONGITUDE] == HOME_LONGITUDE