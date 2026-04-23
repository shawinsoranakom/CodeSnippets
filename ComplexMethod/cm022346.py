async def test_binary_sensor_attributes_state_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test Homeworks binary sensor state changes."""
    entity_id = "binary_sensor.foyer_keypad_morning"
    mock_controller = MagicMock()
    mock_homeworks.return_value = mock_controller

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_homeworks.assert_called_once_with("192.168.0.1", 1234, ANY, None, None)
    hw_callback = mock_homeworks.mock_calls[0][1][2]

    assert entity_id in hass.states.async_entity_ids(BINARY_SENSOR_DOMAIN)

    state = hass.states.get(entity_id)
    assert state.state == STATE_UNKNOWN
    assert state == snapshot

    freezer.tick(KEYPAD_LEDSTATE_POLL_COOLDOWN + 1)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(mock_controller._send.mock_calls) == 1
    assert mock_controller._send.mock_calls[0][1] == ("RKLS, [02:08:02:01]",)

    hw_callback(
        HW_KEYPAD_LED_CHANGED,
        [
            "[02:08:02:01]",
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state == snapshot

    hw_callback(
        HW_KEYPAD_LED_CHANGED,
        [
            "[02:08:02:01]",
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ],
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state == snapshot