async def test_availability(
    hass: HomeAssistant,
    mock_request_status: AsyncMock,
    init_integration: MockConfigEntry,
) -> None:
    """Ensure that we mark the entity's availability properly when network is down / back up."""
    device_slug = slugify(mock_request_status.return_value["UPSNAME"])
    state = hass.states.get(f"sensor.{device_slug}_load")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert pytest.approx(float(state.state)) == 14.0

    # Mock a network error and then trigger an auto-polling event.
    mock_request_status.side_effect = OSError()
    future = utcnow() + UPDATE_INTERVAL
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # Sensors should be marked as unavailable.
    state = hass.states.get(f"sensor.{device_slug}_load")
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Reset the API to return a new status and update.
    mock_request_status.side_effect = None
    mock_request_status.return_value = MOCK_STATUS | {"LOADPCT": "15.0 Percent"}
    future = future + UPDATE_INTERVAL
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    # Sensors should be online now with the new value.
    state = hass.states.get(f"sensor.{device_slug}_load")
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert pytest.approx(float(state.state)) == 15.0