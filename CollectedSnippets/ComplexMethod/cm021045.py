async def test_esphome_device_subscribe_logs(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test configuring a device to subscribe to logs."""
    assert await async_setup_component(hass, "logger", {"logger": {}})
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "fe80::1",
            CONF_PORT: 6053,
            CONF_PASSWORD: "",
        },
        options={CONF_SUBSCRIBE_LOGS: True},
    )
    entry.add_to_hass(hass)
    device = await mock_esphome_device(
        mock_client=mock_client,
        entry=entry,
        device_info={},
    )
    await hass.async_block_till_done()

    async with async_call_logger_set_level(
        "homeassistant.components.esphome", "DEBUG", hass=hass, caplog=caplog
    ):
        assert device.current_log_level == LogLevel.LOG_LEVEL_VERY_VERBOSE

        caplog.set_level(logging.DEBUG)
        device.mock_on_log_message(
            Mock(level=LogLevel.LOG_LEVEL_INFO, message=b"test_log_message")
        )
        await hass.async_block_till_done()
        assert "test_log_message" in caplog.text

        device.mock_on_log_message(
            Mock(level=LogLevel.LOG_LEVEL_ERROR, message=b"test_error_log_message")
        )
        await hass.async_block_till_done()
        assert "test_error_log_message" in caplog.text

        caplog.set_level(logging.ERROR)
        device.mock_on_log_message(
            Mock(level=LogLevel.LOG_LEVEL_DEBUG, message=b"test_debug_log_message")
        )
        await hass.async_block_till_done()
        assert "test_debug_log_message" not in caplog.text

        caplog.set_level(logging.DEBUG)
        device.mock_on_log_message(
            Mock(level=LogLevel.LOG_LEVEL_DEBUG, message=b"test_debug_log_message")
        )
        await hass.async_block_till_done()
        assert "test_debug_log_message" in caplog.text

    async with async_call_logger_set_level(
        "homeassistant.components.esphome", "WARNING", hass=hass, caplog=caplog
    ):
        assert device.current_log_level == LogLevel.LOG_LEVEL_WARN
    async with async_call_logger_set_level(
        "homeassistant.components.esphome", "ERROR", hass=hass, caplog=caplog
    ):
        assert device.current_log_level == LogLevel.LOG_LEVEL_ERROR
    async with async_call_logger_set_level(
        "homeassistant.components.esphome", "INFO", hass=hass, caplog=caplog
    ):
        assert device.current_log_level == LogLevel.LOG_LEVEL_CONFIG