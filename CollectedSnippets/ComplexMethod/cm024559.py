async def test_url_sensor_truncating(
    hass: HomeAssistant,
    mock_fully_kiosk: MagicMock,
    init_integration: MockConfigEntry,
) -> None:
    """Test that long URLs get truncated."""
    state = hass.states.get("sensor.amazon_fire_current_page")
    assert state
    assert state.state == "https://homeassistant.local"
    assert state.attributes.get("full_url") == "https://homeassistant.local"
    assert not state.attributes.get("truncated")

    long_url = "https://01234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789"
    assert len(long_url) > 256

    mock_fully_kiosk.getDeviceInfo.return_value = {
        "currentPage": long_url,
    }
    async_fire_time_changed(hass, dt_util.utcnow() + UPDATE_INTERVAL)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.amazon_fire_current_page")
    assert state
    assert state.state == long_url[0:255]
    assert state.attributes.get("full_url") == long_url
    assert state.attributes.get("truncated")