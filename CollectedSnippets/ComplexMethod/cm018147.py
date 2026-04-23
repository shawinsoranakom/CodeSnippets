async def test_availability_logs(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    multiple_climate_entities: tuple[str, str],
    request: pytest.FixtureRequest,
) -> None:
    """Test that availability status changes are logged correctly."""
    entity_id, mock_fixture = multiple_climate_entities
    mock_instance = request.getfixturevalue(mock_fixture)
    await init_integration(hass)

    caplog.clear()
    mock_instance.get_online.return_value = True
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state != STATE_UNAVAILABLE

    # Make the entity go offline - should log unavailable message
    mock_instance.get_online.return_value = False
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == STATE_UNAVAILABLE
    unavailable_log = f"The entity {entity_id} is unavailable"
    assert unavailable_log in caplog.text

    # Clear logs and update the offline entity again - should NOT log again
    caplog.clear()
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert unavailable_log not in caplog.text

    # Now bring the entity back online - should log back online message
    mock_instance.get_online.return_value = True
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state != STATE_UNAVAILABLE
    available_log = f"The entity {entity_id} is back online"
    assert available_log in caplog.text

    # Clear logs and make update again - should NOT log again
    caplog.clear()
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert available_log not in caplog.text

    # Test offline again to ensure the flag resets properly
    mock_instance.get_online.return_value = False
    state = await update_ac_state(hass, entity_id, mock_instance)
    assert state.state == STATE_UNAVAILABLE
    assert unavailable_log in caplog.text