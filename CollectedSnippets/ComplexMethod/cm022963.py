async def test_color_palette_dynamically_handle_segments(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_wled: MagicMock,
) -> None:
    """Test if a new/deleted segment is dynamically added/removed."""
    assert (segment0 := hass.states.get("select.wled_rgb_light_color_palette"))
    assert segment0.state == "Default"
    assert not hass.states.get("select.wled_rgb_light_segment_1_color_palette")

    return_value = mock_wled.update.return_value
    mock_wled.update.return_value = WLEDDevice.from_dict(
        await async_load_json_object_fixture(hass, "rgb.json", DOMAIN)
    )

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get("select.wled_rgb_light_color_palette"))
    assert segment0.state == "Default"
    assert (
        segment1 := hass.states.get("select.wled_rgb_light_segment_1_color_palette")
    )
    assert segment1.state == "* Random Cycle"

    # Test adding if segment shows up again, including the master entity
    mock_wled.update.return_value = return_value
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get("select.wled_rgb_light_color_palette"))
    assert segment0.state == "Default"
    assert (
        segment1 := hass.states.get("select.wled_rgb_light_segment_1_color_palette")
    )
    assert segment1.state == STATE_UNAVAILABLE