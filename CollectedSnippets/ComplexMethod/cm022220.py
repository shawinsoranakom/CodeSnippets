async def test_light_with_one_non_black_led(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openrgb_device: MagicMock,
) -> None:
    """Test light state when one LED is non-black among black LEDs (on by color)."""
    # Set one LED to red, others to black
    mock_openrgb_device.colors = [RGBColor(*OFF_COLOR), RGBColor(255, 0, 0)]
    mock_openrgb_device.active_mode = 0  # Direct mode (supports colors)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Verify light is on with the non-black LED color
    state = hass.states.get("light.ene_dram")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_COLOR_MODE) == ColorMode.RGB
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [ColorMode.RGB]
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 0, 0)
    assert state.attributes.get(ATTR_BRIGHTNESS) == 255