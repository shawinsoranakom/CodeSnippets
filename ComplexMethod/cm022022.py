async def check_selective_state_update(
    hass: HomeAssistant,
    mock_device: CustomerDevice,
    mock_listener: MockDeviceListener,
    freezer: FrozenDateTimeFactory,
    *,
    entity_id: str,
    dpcode: str,
    initial_state: str,
    updates: dict[str, Any],
    expected_state: str,
    last_reported: str,
) -> None:
    """Test selective state update.

    This test verifies that when an update event comes with properties that do NOT
    include the dpcode (e.g., a battery event for a door sensor),
    the entity state is not changed and last_reported is not updated.
    """
    initial_reported = "2024-01-01T00:00:00+00:00"
    unavailable_reported = "2024-01-01T00:00:10+00:00"
    available_reported = "2024-01-01T00:00:20+00:00"
    assert hass.states.get(entity_id).state == initial_state
    assert hass.states.get(entity_id).last_reported.isoformat() == initial_reported

    # Trigger device offline
    freezer.tick(10)
    await mock_listener.async_mock_offline(mock_device)
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE
    assert hass.states.get(entity_id).last_reported.isoformat() == unavailable_reported

    # Trigger device online
    freezer.tick(10)
    await mock_listener.async_mock_online(mock_device)
    assert hass.states.get(entity_id).state == initial_state
    assert hass.states.get(entity_id).last_reported.isoformat() == available_reported

    # Force update the dpcode and trigger device update without the dpcode
    # in updated properties - state should not change
    freezer.tick(10)
    mock_device.status[dpcode] = None
    await mock_listener.async_send_device_update(mock_device, {})
    assert hass.states.get(entity_id).state == initial_state
    assert hass.states.get(entity_id).last_reported.isoformat() == available_reported

    # Trigger device update with provided updates
    freezer.tick(30)
    await mock_listener.async_send_device_update(mock_device, updates)
    assert hass.states.get(entity_id).state == expected_state
    assert hass.states.get(entity_id).last_reported.isoformat() == last_reported