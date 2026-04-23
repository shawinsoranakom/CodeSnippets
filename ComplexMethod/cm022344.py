async def test_keypad_events(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
) -> None:
    """Test Homeworks keypad events."""
    release_events = async_capture_events(hass, EVENT_BUTTON_RELEASE)
    press_events = async_capture_events(hass, EVENT_BUTTON_PRESS)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_homeworks.assert_called_once_with("192.168.0.1", 1234, ANY, None, None)
    hw_callback = mock_homeworks.mock_calls[0][1][2]

    hw_callback(HW_BUTTON_PRESSED, ["[02:08:02:01]", 1])
    await hass.async_block_till_done()
    assert len(press_events) == 1
    assert len(release_events) == 0
    assert press_events[0].data == {
        "id": "foyer_keypad",
        "name": "Foyer Keypad",
        "button": 1,
    }
    assert press_events[0].event_type == "homeworks_button_press"

    hw_callback(HW_BUTTON_RELEASED, ["[02:08:02:01]", 1])
    await hass.async_block_till_done()
    assert len(press_events) == 1
    assert len(release_events) == 1
    assert release_events[0].data == {
        "id": "foyer_keypad",
        "name": "Foyer Keypad",
        "button": 1,
    }
    assert release_events[0].event_type == "homeworks_button_release"

    hw_callback("unsupported", ["[02:08:02:01]", 1])
    await hass.async_block_till_done()
    assert len(press_events) == 1
    assert len(release_events) == 1