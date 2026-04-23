async def test_single_segment_behavior(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_wled: MagicMock,
) -> None:
    """Test the behavior of the integration with a single segment."""
    device = mock_wled.update.return_value

    assert not hass.states.get("light.wled_rgb_light_main")
    assert (state := hass.states.get("light.wled_rgb_light"))
    assert state.state == STATE_ON

    # Test segment brightness takes main into account
    device.state.brightness = 100
    device.state.segments[0].brightness = 255
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("light.wled_rgb_light"))
    assert state.attributes.get(ATTR_BRIGHTNESS) == 100

    # Test segment is off when main is off
    device.state.on = False
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get("light.wled_rgb_light")
    assert state
    assert state.state == STATE_OFF

    # Test main is turned off when turning off a single segment
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.wled_rgb_light", ATTR_TRANSITION: 5},
        blocking=True,
    )
    assert mock_wled.master.call_count == 1
    mock_wled.master.assert_called_with(
        on=False,
        transition=50,
    )

    # Test main is turned on when turning on a single segment, and segment
    # brightness is set to 255.
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.wled_rgb_light",
            ATTR_TRANSITION: 5,
            ATTR_BRIGHTNESS: 42,
        },
        blocking=True,
    )
    assert mock_wled.segment.call_count == 1
    assert mock_wled.master.call_count == 2
    mock_wled.segment.assert_called_with(on=True, segment_id=0, brightness=255)
    mock_wled.master.assert_called_with(on=True, transition=50, brightness=42)