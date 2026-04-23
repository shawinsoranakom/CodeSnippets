async def async_pipeline_from_audio_stream(
        hass: HomeAssistant,
        context: Context,
        *args,
        device_id: str | None,
        tts_audio_output: str | dict[str, Any] | None,
        **kwargs,
    ):
        assert context.user_id == voip_user_id
        assert device_id == voip_device.device_id

        # voip can only stream WAV
        assert tts_audio_output == {
            tts.ATTR_PREFERRED_FORMAT: "wav",
            tts.ATTR_PREFERRED_SAMPLE_RATE: 16000,
            tts.ATTR_PREFERRED_SAMPLE_CHANNELS: 1,
            tts.ATTR_PREFERRED_SAMPLE_BYTES: 2,
        }

        stt_stream = kwargs["stt_stream"]
        event_callback = kwargs["event_callback"]
        in_command = False
        async for chunk in stt_stream:
            # Stream will end when VAD detects end of "speech"
            assert chunk != bad_chunk
            if sum(chunk) > 0:
                in_command = True
            elif in_command:
                break  # done with command

        # Test empty data
        event_callback(
            assist_pipeline.PipelineEvent(
                type="not-used",
                data={},
            )
        )

        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.STT_START,
                data={"engine": "test", "metadata": {}},
            )
        )

        assert satellite.state == AssistSatelliteState.LISTENING

        # Fake STT result
        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.STT_END,
                data={"stt_output": {"text": "fake-text"}},
            )
        )

        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.INTENT_START,
                data={
                    "engine": "test",
                    "language": hass.config.language,
                    "intent_input": "fake-text",
                    "conversation_id": None,
                    "device_id": None,
                },
            )
        )

        assert satellite.state == AssistSatelliteState.PROCESSING

        # Fake intent result
        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.INTENT_END,
                data={
                    "intent_output": {
                        "conversation_id": "fake-conversation",
                    }
                },
            )
        )

        # Fake tts result
        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.TTS_START,
                data={
                    "engine": "test",
                    "language": hass.config.language,
                    "voice": "test",
                    "tts_input": "fake-text",
                },
            )
        )

        assert satellite.state == AssistSatelliteState.RESPONDING

        # Proceed with media output
        mock_tts_result_stream = MockResultStream(hass, "wav", _empty_wav())
        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.TTS_END,
                data={"tts_output": {"token": mock_tts_result_stream.token}},
            )
        )

        event_callback(
            assist_pipeline.PipelineEvent(
                type=assist_pipeline.PipelineEventType.RUN_END
            )
        )