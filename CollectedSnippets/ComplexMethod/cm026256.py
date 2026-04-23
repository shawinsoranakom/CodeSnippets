def on_pipeline_event(self, event: PipelineEvent) -> None:
        """Handle pipeline events."""
        try:
            event_type = _VOICE_ASSISTANT_EVENT_TYPES.from_hass(event.type)
        except KeyError:
            _LOGGER.debug("Received unknown pipeline event type: %s", event.type)
            return

        data_to_send: dict[str, Any] = {}
        if event_type == VoiceAssistantEventType.VOICE_ASSISTANT_STT_START:
            self._entry_data.async_set_assist_pipeline_state(True)
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_STT_END:
            assert event.data is not None
            data_to_send = {"text": event.data["stt_output"]["text"]}
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_INTENT_PROGRESS:
            if (
                not event.data
                or ("tts_start_streaming" not in event.data)
                or (not event.data["tts_start_streaming"])
            ):
                # ESPHome only needs to know if early TTS streaming is available
                return

            data_to_send = {"tts_start_streaming": "1"}
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_INTENT_END:
            assert event.data is not None
            data_to_send = {
                "conversation_id": event.data["intent_output"]["conversation_id"],
                "continue_conversation": str(
                    int(event.data["intent_output"]["continue_conversation"])
                ),
            }
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_TTS_START:
            assert event.data is not None
            data_to_send = {"text": event.data["tts_input"]}
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_TTS_END:
            assert event.data is not None
            if tts_output := event.data["tts_output"]:
                path = tts_output["url"]
                url = async_process_play_media_url(self.hass, path)
                data_to_send = {"url": url}

                assert self._entry_data.device_info is not None
                feature_flags = (
                    self._entry_data.device_info.voice_assistant_feature_flags_compat(
                        self._entry_data.api_version
                    )
                )
                if feature_flags & VoiceAssistantFeature.SPEAKER and (
                    stream := tts.async_get_stream(self.hass, tts_output["token"])
                ):
                    self._tts_streaming_task = (
                        self.config_entry.async_create_background_task(
                            self.hass,
                            self._stream_tts_audio(stream),
                            "esphome_voice_assistant_tts",
                        )
                    )
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_WAKE_WORD_END:
            assert event.data is not None
            if not event.data["wake_word_output"]:
                event_type = VoiceAssistantEventType.VOICE_ASSISTANT_ERROR
                data_to_send = {
                    "code": "no_wake_word",
                    "message": "No wake word detected",
                }
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_ERROR:
            assert event.data is not None
            data_to_send = {
                "code": event.data["code"],
                "message": event.data["message"],
            }
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_RUN_START:
            assert event.data is not None
            if tts_output := event.data.get("tts_output"):
                path = tts_output["url"]
                url = async_process_play_media_url(self.hass, path)
                data_to_send = {"url": url}
        elif event_type == VoiceAssistantEventType.VOICE_ASSISTANT_RUN_END:
            if self._tts_streaming_task is None:
                # No TTS
                self._entry_data.async_set_assist_pipeline_state(False)

        self.cli.send_voice_assistant_event(event_type, data_to_send)