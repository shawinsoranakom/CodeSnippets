async def test_previous_values_updated_on_refresh(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openrgb_device: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that previous values are updated when device state changes externally."""
    # Start with device in Direct mode with red color at full brightness
    mock_openrgb_device.active_mode = 0
    mock_openrgb_device.colors = [RGBColor(255, 0, 0), RGBColor(255, 0, 0)]

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Verify initial state
    state = hass.states.get("light.ene_dram")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_RGB_COLOR) == (255, 0, 0)  # Red
    assert state.attributes.get(ATTR_BRIGHTNESS) == 255
    assert state.attributes.get(ATTR_EFFECT) == EFFECT_OFF  # Direct mode

    # Simulate external change to green at 50% brightness in Breathing mode
    # (e.g., via the OpenRGB application)
    mock_openrgb_device.active_mode = 3  # Breathing mode
    mock_openrgb_device.colors = [RGBColor(0, 128, 0), RGBColor(0, 128, 0)]

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify new state
    state = hass.states.get("light.ene_dram")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_RGB_COLOR) == (0, 255, 0)  # Green
    assert state.attributes.get(ATTR_BRIGHTNESS) == 128  # 50% brightness
    assert state.attributes.get(ATTR_EFFECT) == "breathing"

    # Simulate external change to Off mode
    mock_openrgb_device.active_mode = 1

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify light is off
    state = hass.states.get("light.ene_dram")
    assert state
    assert state.state == STATE_OFF

    # Turn on without parameters - should restore most recent state (green, 50%, Breathing)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.ene_dram"},
        blocking=True,
    )

    mock_openrgb_device.set_mode.assert_called_once_with("Breathing")
    mock_openrgb_device.set_color.assert_called_once_with(RGBColor(0, 128, 0), True)