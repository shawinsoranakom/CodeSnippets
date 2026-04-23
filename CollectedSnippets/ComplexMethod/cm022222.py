async def test_light_with_no_effects(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_openrgb_device: MagicMock,
) -> None:
    """Test light with a device that has no effects."""
    # Keep only no-effect modes in the device
    mock_openrgb_device.modes = [
        mode
        for mode in mock_openrgb_device.modes
        if mode.name in {OpenRGBMode.OFF, OpenRGBMode.DIRECT, OpenRGBMode.STATIC}
    ]

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Verify light entity doesn't have EFFECT feature
    state = hass.states.get("light.ene_dram")
    assert state

    assert state.attributes.get(ATTR_SUPPORTED_FEATURES) == 0
    assert state.attributes.get(ATTR_EFFECT) is None

    # Verify the light is still functional (can be turned on/off)
    assert state.state == STATE_ON