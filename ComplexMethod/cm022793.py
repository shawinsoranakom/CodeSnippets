async def test_tracker_arrive_home(hass: HomeAssistant) -> None:
    """Test transition from not_home to home."""
    await async_mock_config_entry(hass)
    await async_inject_broadcast(hass, MAC_RPA_VALID_1, b"1")
    state = hass.states.get("device_tracker.private_ble_device_000000")
    assert state
    assert state.state == "home"
    assert state.attributes["current_address"] == "40:01:02:0a:c4:a6"
    assert state.attributes["source"] == "local"

    await async_inject_broadcast(hass, MAC_STATIC, b"1")
    state = hass.states.get("device_tracker.private_ble_device_000000")
    assert state
    assert state.state == "home"

    # Test same wrong mac address again to exercise some caching
    await async_inject_broadcast(hass, MAC_STATIC, b"2")
    state = hass.states.get("device_tracker.private_ble_device_000000")
    assert state
    assert state.state == "home"

    # And test original mac address again.
    # Use different mfr data so that event bubbles up
    await async_inject_broadcast(hass, MAC_RPA_VALID_1, b"2")
    state = hass.states.get("device_tracker.private_ble_device_000000")
    assert state
    assert state.state == "home"
    assert state.attributes["current_address"] == "40:01:02:0a:c4:a6"