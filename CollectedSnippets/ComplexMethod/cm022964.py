async def test_dynamically_handle_segments(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_wled: MagicMock,
) -> None:
    """Test if a new/deleted segment is dynamically added/removed."""
    assert (segment0 := hass.states.get("light.wled_rgb_light"))
    assert segment0.state == STATE_ON
    assert not hass.states.get("light.wled_rgb_light_main")
    assert not hass.states.get("light.wled_rgb_light_segment_1")

    return_value = mock_wled.update.return_value
    mock_wled.update.return_value = WLEDDevice.from_dict(
        await async_load_json_object_fixture(hass, "rgb.json", DOMAIN)
    )

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (main := hass.states.get("light.wled_rgb_light_main"))
    assert main.state == STATE_ON
    assert (segment0 := hass.states.get("light.wled_rgb_light"))
    assert segment0.state == STATE_ON
    assert (segment1 := hass.states.get("light.wled_rgb_light_segment_1"))
    assert segment1.state == STATE_ON

    # Test adding if segment shows up again, including the main entity
    mock_wled.update.return_value = return_value
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (main := hass.states.get("light.wled_rgb_light_main"))
    assert main.state == STATE_UNAVAILABLE
    assert (segment0 := hass.states.get("light.wled_rgb_light"))
    assert segment0.state == STATE_ON
    assert (segment1 := hass.states.get("light.wled_rgb_light_segment_1"))
    assert segment1.state == STATE_UNAVAILABLE