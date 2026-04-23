async def test_process_integration_platforms_non_compliant(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture, process_platform: Callable
) -> None:
    """Test processing integrations using with a non-compliant platform."""
    loaded_platform = Mock()
    mock_platform(hass, "loaded_unique_880.platform_to_check", loaded_platform)
    hass.config.components.add("loaded_unique_880")

    event_platform = Mock()
    mock_platform(hass, "event_unique_990.platform_to_check", event_platform)

    processed = []

    await async_process_integration_platforms(
        hass, "platform_to_check", process_platform
    )
    await hass.async_block_till_done()

    assert len(processed) == 0
    assert "Exception in " in caplog.text
    assert "platform_to_check" in caplog.text
    assert "Non-compliant platform" in caplog.text
    assert "loaded_unique_880" in caplog.text
    caplog.clear()

    hass.bus.async_fire(EVENT_COMPONENT_LOADED, {ATTR_COMPONENT: "event_unique_990"})
    await hass.async_block_till_done()

    assert "Exception in " in caplog.text
    assert "platform_to_check" in caplog.text
    assert "Non-compliant platform" in caplog.text
    assert "event_unique_990" in caplog.text

    assert len(processed) == 0