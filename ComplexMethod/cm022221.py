async def test_light_with_non_color_mode(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openrgb_device: MagicMock,
) -> None:
    """Test light state with a mode that doesn't support colors."""
    # Set to Rainbow mode (doesn't support colors)
    mock_openrgb_device.active_mode = 6

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Verify light is on with ON/OFF mode
    state = hass.states.get("light.ene_dram")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == LightEntityFeature.EFFECT
    assert state.attributes.get(ATTR_EFFECT) == "rainbow"
    assert state.attributes.get(ATTR_COLOR_MODE) == ColorMode.ONOFF
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [ColorMode.ONOFF]
    assert state.attributes.get(ATTR_RGB_COLOR) is None
    assert state.attributes.get(ATTR_BRIGHTNESS) is None