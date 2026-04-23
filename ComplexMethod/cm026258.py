async def handle_pipeline_start(
        self,
        conversation_id: str,
        flags: int,
        audio_settings: VoiceAssistantAudioSettings,
        wake_word_phrase: str | None,
    ) -> int | None:
        """Handle pipeline run request."""
        # Clear audio queue
        while not self._audio_queue.empty():
            await self._audio_queue.get()

        if self._tts_streaming_task is not None:
            # Cancel current TTS response
            self._tts_streaming_task.cancel()
            self._tts_streaming_task = None

        # API or UDP output audio
        port: int = 0
        assert self._entry_data.device_info is not None
        feature_flags = (
            self._entry_data.device_info.voice_assistant_feature_flags_compat(
                self._entry_data.api_version
            )
        )
        if (feature_flags & VoiceAssistantFeature.SPEAKER) and not (
            feature_flags & VoiceAssistantFeature.API_AUDIO
        ):
            port = await self._start_udp_server()
            _LOGGER.debug("Started UDP server on port %s", port)

        # Device triggered pipeline (wake word, etc.)
        if flags & VoiceAssistantCommandFlag.USE_WAKE_WORD:
            start_stage = PipelineStage.WAKE_WORD
        else:
            start_stage = PipelineStage.STT

        end_stage = PipelineStage.TTS

        if feature_flags & VoiceAssistantFeature.SPEAKER:
            # Stream WAV audio
            self._attr_tts_options = {
                tts.ATTR_PREFERRED_FORMAT: "wav",
                tts.ATTR_PREFERRED_SAMPLE_RATE: 16000,
                tts.ATTR_PREFERRED_SAMPLE_CHANNELS: 1,
                tts.ATTR_PREFERRED_SAMPLE_BYTES: 2,
            }
        else:
            # ANNOUNCEMENT format from media player
            self._update_tts_format()

        # Run the appropriate pipeline.
        self._active_pipeline_index = 0

        maybe_pipeline_index = 0
        while ww_entity_id := self.get_wake_word_entity(maybe_pipeline_index):
            if (
                ww_state := self.hass.states.get(ww_entity_id)
            ) and ww_state.state == wake_word_phrase:
                # First match
                self._active_pipeline_index = maybe_pipeline_index
                break

            # Try next wake word select
            maybe_pipeline_index += 1

        _LOGGER.debug(
            "Running pipeline %s from %s to %s",
            self._active_pipeline_index + 1,
            start_stage,
            end_stage,
        )
        self._pipeline_task = self.config_entry.async_create_background_task(
            self.hass,
            self.async_accept_pipeline_from_satellite(
                audio_stream=self._wrap_audio_stream(),
                start_stage=start_stage,
                end_stage=end_stage,
                wake_word_phrase=wake_word_phrase,
            ),
            "esphome_assist_satellite_pipeline",
        )
        self._pipeline_task.add_done_callback(
            lambda _future: self.handle_pipeline_finished()
        )

        return port