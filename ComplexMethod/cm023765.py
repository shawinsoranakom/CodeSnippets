async def test_service_name(hass: HomeAssistant) -> None:
    """Test loading service info."""
    with patch(
        "homeassistant.components.wyoming.data.AsyncTcpClient",
        MockAsyncTcpClient([STT_INFO.event()]),
    ):
        service = await WyomingService.create("localhost", 1234)
        assert service is not None
        assert service.get_name() == STT_INFO.asr[0].name

    with patch(
        "homeassistant.components.wyoming.data.AsyncTcpClient",
        MockAsyncTcpClient([TTS_INFO.event()]),
    ):
        service = await WyomingService.create("localhost", 1234)
        assert service is not None
        assert service.get_name() == TTS_INFO.tts[0].name

    with patch(
        "homeassistant.components.wyoming.data.AsyncTcpClient",
        MockAsyncTcpClient([WAKE_WORD_INFO.event()]),
    ):
        service = await WyomingService.create("localhost", 1234)
        assert service is not None
        assert service.get_name() == WAKE_WORD_INFO.wake[0].name

    with patch(
        "homeassistant.components.wyoming.data.AsyncTcpClient",
        MockAsyncTcpClient([SATELLITE_INFO.event()]),
    ):
        service = await WyomingService.create("localhost", 1234)
        assert service is not None
        assert service.get_name() == SATELLITE_INFO.satellite.name