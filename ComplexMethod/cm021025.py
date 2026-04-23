async def async_pipeline_from_audio_stream(*args, device_id, **kwargs):
        assert device_id == dev.id

        stt_stream = kwargs["stt_stream"]

        chunks = [chunk async for chunk in stt_stream]

        # Verify test API audio
        assert chunks == [b"test-mic"]

        event_callback = kwargs["event_callback"]

        # Test unknown event type
        event_callback(
            PipelineEvent(
                type="unknown-event",
                data={},
            )
        )

        mock_client.send_voice_assistant_event.assert_not_called()

        # Test error event
        event_callback(
            PipelineEvent(
                type=PipelineEventType.ERROR,
                data={"code": "test-error-code", "message": "test-error-message"},
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_ERROR,
            {"code": "test-error-code", "message": "test-error-message"},
        )

        # Wake word
        assert satellite.state == AssistSatelliteState.IDLE

        event_callback(
            PipelineEvent(
                type=PipelineEventType.WAKE_WORD_START,
                data={
                    "entity_id": "test-wake-word-entity-id",
                    "metadata": {},
                    "timeout": 0,
                },
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_WAKE_WORD_START,
            {},
        )

        # Test no wake word detected
        event_callback(
            PipelineEvent(
                type=PipelineEventType.WAKE_WORD_END, data={"wake_word_output": {}}
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_ERROR,
            {"code": "no_wake_word", "message": "No wake word detected"},
        )

        # Correct wake word detection
        event_callback(
            PipelineEvent(
                type=PipelineEventType.WAKE_WORD_END,
                data={"wake_word_output": {"wake_word_phrase": "test-wake-word"}},
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_WAKE_WORD_END,
            {},
        )

        # STT
        event_callback(
            PipelineEvent(
                type=PipelineEventType.STT_START,
                data={"engine": "test-stt-engine", "metadata": {}},
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_STT_START,
            {},
        )
        assert satellite.state == AssistSatelliteState.LISTENING

        event_callback(
            PipelineEvent(
                type=PipelineEventType.STT_END,
                data={"stt_output": {"text": "test-stt-text"}},
            )
        )
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_STT_END,
            {"text": "test-stt-text"},
        )

        # Intent
        event_callback(
            PipelineEvent(
                type=PipelineEventType.INTENT_START,
                data={
                    "engine": "test-intent-engine",
                    "language": hass.config.language,
                    "intent_input": "test-intent-text",
                    "conversation_id": conversation_id,
                    "device_id": device_id,
                },
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_INTENT_START,
            {},
        )
        assert satellite.state == AssistSatelliteState.PROCESSING

        event_callback(
            PipelineEvent(
                type=PipelineEventType.INTENT_PROGRESS,
                data={"tts_start_streaming": "1"},
            )
        )
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_INTENT_PROGRESS,
            {"tts_start_streaming": "1"},
        )

        event_callback(
            PipelineEvent(
                type=PipelineEventType.INTENT_END,
                data={
                    "intent_output": conversation.ConversationResult(
                        response=intent_helper.IntentResponse("en"),
                        conversation_id=conversation_id,
                        continue_conversation=True,
                    ).as_dict()
                },
            )
        )
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_INTENT_END,
            {
                "conversation_id": conversation_id,
                "continue_conversation": "1",
            },
        )

        # TTS
        event_callback(
            PipelineEvent(
                type=PipelineEventType.TTS_START,
                data={
                    "engine": "test-stt-engine",
                    "language": hass.config.language,
                    "voice": "test-voice",
                    "tts_input": "test-tts-text",
                },
            )
        )

        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_TTS_START,
            {"text": "test-tts-text"},
        )
        assert satellite.state == AssistSatelliteState.RESPONDING

        # Should return mock_wav audio
        mock_tts_result_stream = MockResultStream(hass, "wav", mock_wav)
        event_callback(
            PipelineEvent(
                type=PipelineEventType.TTS_END,
                data={
                    "tts_output": {
                        "media_id": "test-media-id",
                        "url": mock_tts_result_stream.url,
                        "token": mock_tts_result_stream.token,
                    }
                },
            )
        )
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_TTS_END,
            {"url": get_url(hass) + mock_tts_result_stream.url},
        )

        event_callback(
            PipelineEvent(
                type=PipelineEventType.RUN_START,
                data={
                    "tts_output": {
                        "media_id": "test-media-id",
                        "url": mock_tts_result_stream.url,
                        "token": mock_tts_result_stream.token,
                    }
                },
            )
        )
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_RUN_START,
            {"url": get_url(hass) + mock_tts_result_stream.url},
        )

        event_callback(PipelineEvent(type=PipelineEventType.RUN_END))
        assert mock_client.send_voice_assistant_event.call_args_list[-1].args == (
            VoiceAssistantEventType.VOICE_ASSISTANT_RUN_END,
            {},
        )

        # Allow TTS streaming to proceed
        stream_tts_audio_ready.set()