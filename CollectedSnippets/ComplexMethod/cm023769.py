async def test_on_pipeline_event_ignores_disconnected_client(
    hass: HomeAssistant,
) -> None:
    """Test that ``on_pipeline_event`` is a no-op after the client disconnected.

    Previously this path hit ``assert self._client is not None``, which raised
    ``AssertionError`` once per event while the pipeline kept running after a
    disconnect, contributing to the memory leak in 2026.4.0.
    """
    events: list[Event] = [
        RunPipeline(
            start_stage=PipelineStage.WAKE, end_stage=PipelineStage.TTS
        ).event(),
    ]

    pipeline_event = asyncio.Event()

    def _async_pipeline_from_audio_stream(*args: Any, **kwargs: Any) -> None:
        pipeline_event.set()

    with (
        patch(
            "homeassistant.components.wyoming.data.load_wyoming_info",
            return_value=SATELLITE_INFO,
        ),
        patch(
            "homeassistant.components.wyoming.assist_satellite.AsyncTcpClient",
            SatelliteAsyncTcpClient(events),
        ) as mock_client,
        patch(
            "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream",
            wraps=_async_pipeline_from_audio_stream,
        ) as mock_run_pipeline,
    ):
        await setup_config_entry(hass)

        async with asyncio.timeout(1):
            await pipeline_event.wait()
            await mock_client.connect_event.wait()
            await mock_client.run_satellite_event.wait()

        event_callback = mock_run_pipeline.call_args.kwargs["event_callback"]
        # event_callback is the base class's bound _internal_on_pipeline_event,
        # so we can reach the satellite entity from there.
        satellite: WyomingAssistSatellite = event_callback.__self__

        # Simulate the disconnect race: the pipeline is still firing events
        # but the TCP client has already been torn down.
        satellite._client = None

        # Must not raise, must not spawn a background write task.
        for event_type in (
            assist_pipeline.PipelineEventType.WAKE_WORD_START,
            assist_pipeline.PipelineEventType.STT_START,
            assist_pipeline.PipelineEventType.STT_END,
            assist_pipeline.PipelineEventType.TTS_START,
            assist_pipeline.PipelineEventType.ERROR,
        ):
            event_callback(
                assist_pipeline.PipelineEvent(
                    event_type,
                    {
                        "metadata": {"language": "en"},
                        "stt_output": {"text": "ignored"},
                        "tts_input": "ignored",
                        "code": "err",
                        "message": "ignored",
                        "timestamp": 0,
                    },
                )
            )

        # RUN_END must still update bookkeeping even with no client.
        satellite._is_pipeline_running = True
        satellite._pipeline_ended_event.clear()
        event_callback(
            assist_pipeline.PipelineEvent(assist_pipeline.PipelineEventType.RUN_END, {})
        )
        assert not satellite._is_pipeline_running
        assert satellite._pipeline_ended_event.is_set()

        # Flush any stray background tasks before asserting on side effects.
        await hass.async_block_till_done()

        # If the guard did not hold, the mock client would have observed
        # ``Detect``, ``Transcribe``, ``Transcript``, ``Synthesize`` and
        # ``Error`` events.
        assert not mock_client.detect_event.is_set()
        assert not mock_client.transcribe_event.is_set()
        assert not mock_client.transcript_event.is_set()
        assert not mock_client.synthesize_event.is_set()
        assert not mock_client.error_event.is_set()