async def async_accept_pipeline_from_satellite(
        self,
        audio_stream: AsyncIterable[bytes],
        start_stage: PipelineStage = PipelineStage.STT,
        end_stage: PipelineStage = PipelineStage.TTS,
        wake_word_phrase: str | None = None,
    ) -> None:
        """Triggers an Assist pipeline in Home Assistant from a satellite."""
        await self._cancel_running_pipeline()

        # Consume system prompt in first pipeline
        extra_system_prompt = self._extra_system_prompt
        self._extra_system_prompt = None

        if self._wake_word_intercept_future and start_stage in (
            PipelineStage.WAKE_WORD,
            PipelineStage.STT,
        ):
            if start_stage == PipelineStage.WAKE_WORD:
                self._wake_word_intercept_future.set_exception(
                    AssistSatelliteError(
                        "Only on-device wake words currently supported"
                    )
                )
                return

            # Intercepting wake word and immediately end pipeline
            _LOGGER.debug(
                "Intercepted wake word: %s (entity_id=%s)",
                wake_word_phrase,
                self.entity_id,
            )

            if wake_word_phrase is None:
                self._wake_word_intercept_future.set_exception(
                    AssistSatelliteError("No wake word phrase provided")
                )
            else:
                self._wake_word_intercept_future.set_result(wake_word_phrase)
            self._internal_on_pipeline_event(PipelineEvent(PipelineEventType.RUN_END))
            return

        if (self._ask_question_future is not None) and (
            start_stage == PipelineStage.STT
        ):
            end_stage = PipelineStage.STT

        device_id = self.registry_entry.device_id if self.registry_entry else None

        # Refresh context if necessary
        if (
            (self._context is None)
            or (self._context_set is None)
            or ((time.time() - self._context_set) > entity.CONTEXT_RECENT_TIME_SECONDS)
        ):
            self.async_set_context(Context())

        assert self._context is not None

        # Set entity state based on pipeline events
        self._run_has_tts = False

        assert self.platform.config_entry is not None

        with chat_session.async_get_chat_session(
            self.hass, self._conversation_id
        ) as session:
            # Store the conversation ID. If it is no longer valid, get_chat_session will reset it
            self._conversation_id = session.conversation_id
            self._pipeline_task = (
                self.platform.config_entry.async_create_background_task(
                    self.hass,
                    async_pipeline_from_audio_stream(
                        self.hass,
                        context=self._context,
                        event_callback=self._internal_on_pipeline_event,
                        stt_metadata=stt.SpeechMetadata(
                            language="",  # set in async_pipeline_from_audio_stream
                            format=stt.AudioFormats.WAV,
                            codec=stt.AudioCodecs.PCM,
                            bit_rate=stt.AudioBitRates.BITRATE_16,
                            sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                            channel=stt.AudioChannels.CHANNEL_MONO,
                        ),
                        stt_stream=audio_stream,
                        pipeline_id=self._resolve_pipeline(),
                        conversation_id=session.conversation_id,
                        device_id=device_id,
                        satellite_id=self.entity_id,
                        tts_audio_output=self.tts_options,
                        wake_word_phrase=wake_word_phrase,
                        audio_settings=AudioSettings(
                            silence_seconds=self._resolve_vad_sensitivity()
                        ),
                        start_stage=start_stage,
                        end_stage=end_stage,
                        conversation_extra_system_prompt=extra_system_prompt,
                    ),
                    f"{self.entity_id}_pipeline",
                )
            )

            try:
                await self._pipeline_task
            finally:
                self._pipeline_task = None