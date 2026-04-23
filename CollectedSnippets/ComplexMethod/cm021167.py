async def test_entity_availability(
    hass: HomeAssistant, mock_light: AsyncMock, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that entity availability updates based on device connection status."""

    entity_id = f"light.{mock_light.name.lower().replace(' ', '_')}"

    # Initially connected
    mock_light.pyvlx.get_connected.return_value = True
    await update_callback_entity(hass, mock_light)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE

    # Simulate disconnection
    mock_light.pyvlx.get_connected.return_value = False
    await update_callback_entity(hass, mock_light)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert caplog.text.count(f"Entity {entity_id} is unavailable") == 1

    # Simulate disconnection, check we don't log again
    mock_light.pyvlx.get_connected.return_value = False
    await update_callback_entity(hass, mock_light)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    assert caplog.text.count(f"Entity {entity_id} is unavailable") == 1

    # Simulate reconnection
    mock_light.pyvlx.get_connected.return_value = True
    await update_callback_entity(hass, mock_light)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert caplog.text.count(f"Entity {entity_id} is back online") == 1

    # Simulate reconnection, check we don't log again
    mock_light.pyvlx.get_connected.return_value = True
    await update_callback_entity(hass, mock_light)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert caplog.text.count(f"Entity {entity_id} is back online") == 1