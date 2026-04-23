async def test_binary_sensor_callback(
    hass: HomeAssistant,
    mock_satel: AsyncMock,
    mock_config_entry_with_subentries: MockConfigEntry,
) -> None:
    """Test binary sensors correctly change state after a callback from the panel."""
    await setup_integration(hass, mock_config_entry_with_subentries)

    assert hass.states.get("binary_sensor.zone").state == STATE_OFF
    assert hass.states.get("binary_sensor.output").state == STATE_OFF

    _, zone_update_method, output_update_method = get_monitor_callbacks(mock_satel)

    output_update_method({1: 1})
    zone_update_method({1: 1})
    assert hass.states.get("binary_sensor.zone").state == STATE_ON
    assert hass.states.get("binary_sensor.output").state == STATE_ON

    output_update_method({1: 0})
    zone_update_method({1: 0})
    assert hass.states.get("binary_sensor.zone").state == STATE_OFF
    assert hass.states.get("binary_sensor.output").state == STATE_OFF

    # The client library should always report all entries, but test that we set the status correctly if it doesn't
    output_update_method({2: 1})
    zone_update_method({2: 1})
    assert hass.states.get("binary_sensor.zone").state == STATE_UNKNOWN
    assert hass.states.get("binary_sensor.output").state == STATE_UNKNOWN