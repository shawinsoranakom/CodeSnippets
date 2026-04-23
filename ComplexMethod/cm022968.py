async def test_switch_dynamically_handle_segments(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_wled: MagicMock,
) -> None:
    """Test if a new/deleted segment is dynamically added/removed."""

    assert (segment0 := hass.states.get("switch.wled_rgb_light_reverse"))
    assert segment0.state == STATE_OFF
    assert not hass.states.get("switch.wled_rgb_light_segment_1_reverse")

    # Test adding a segment dynamically...
    return_value = mock_wled.update.return_value
    mock_wled.update.return_value = WLEDDevice.from_dict(
        await async_load_json_object_fixture(hass, "rgb.json", DOMAIN)
    )

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get("switch.wled_rgb_light_reverse"))
    assert segment0.state == STATE_OFF
    assert (segment1 := hass.states.get("switch.wled_rgb_light_segment_1_reverse"))
    assert segment1.state == STATE_ON

    # Test remove segment again...
    mock_wled.update.return_value = return_value
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get("switch.wled_rgb_light_reverse"))
    assert segment0.state == STATE_OFF
    assert (segment1 := hass.states.get("switch.wled_rgb_light_segment_1_reverse"))
    assert segment1.state == STATE_UNAVAILABLE