def on_pipeline_event(self, event: PipelineEvent) -> None:
        """Set state based on pipeline stage."""
        if event.type == assist_pipeline.PipelineEventType.RUN_END:
            # Pipeline run is complete — always update bookkeeping state
            # even after a disconnect so follow-up reconnects don't retain
            # stale _is_pipeline_running / _pipeline_ended_event state.
            self._is_pipeline_running = False
            self._pipeline_ended_event.set()
            self.device.set_is_active(False)
            self._tts_stream_token = None
            self._is_tts_streaming = False

        if self._client is None:
            # Satellite disconnected, don't try to write to the client
            return

        if event.type == assist_pipeline.PipelineEventType.RUN_START:
            if event.data and (tts_output := event.data["tts_output"]):
                # Get stream token early.
                # If "tts_start_streaming" is True in INTENT_PROGRESS event, we
                # can start streaming TTS before the TTS_END event.
                self._tts_stream_token = tts_output["token"]
                self._is_tts_streaming = False
        elif event.type == assist_pipeline.PipelineEventType.WAKE_WORD_START:
            self.config_entry.async_create_background_task(
                self.hass,
                self._client.write_event(Detect().event()),
                f"{self.entity_id} {event.type}",
            )
        elif event.type == assist_pipeline.PipelineEventType.WAKE_WORD_END:
            # Wake word detection
            # Inform client of wake word detection
            if event.data and (wake_word_output := event.data.get("wake_word_output")):
                detection = Detection(
                    name=wake_word_output["wake_word_id"],
                    timestamp=wake_word_output.get("timestamp"),
                )
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(detection.event()),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.STT_START:
            # Speech-to-text
            self.device.set_is_active(True)

            if event.data:
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(
                        Transcribe(language=event.data["metadata"]["language"]).event()
                    ),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.STT_VAD_START:
            # User started speaking
            if event.data:
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(
                        VoiceStarted(timestamp=event.data["timestamp"]).event()
                    ),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.STT_VAD_END:
            # User stopped speaking
            if event.data:
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(
                        VoiceStopped(timestamp=event.data["timestamp"]).event()
                    ),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.STT_END:
            # Speech-to-text transcript
            if event.data:
                # Inform client of transript
                stt_text = event.data["stt_output"]["text"]
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(Transcript(text=stt_text).event()),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.INTENT_PROGRESS:
            if (
                event.data
                and event.data.get("tts_start_streaming")
                and self._tts_stream_token
                and (stream := tts.async_get_stream(self.hass, self._tts_stream_token))
            ):
                # Start streaming TTS early (before TTS_END).
                self._is_tts_streaming = True
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._stream_tts(stream),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.TTS_START:
            # Text-to-speech text
            if event.data:
                # Inform client of text
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(
                        Synthesize(
                            text=event.data["tts_input"],
                            voice=SynthesizeVoice(
                                name=event.data.get("voice"),
                                language=event.data.get("language"),
                            ),
                        ).event()
                    ),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.TTS_END:
            # TTS stream
            if (
                event.data
                and (tts_output := event.data["tts_output"])
                and not self._is_tts_streaming
                and (stream := tts.async_get_stream(self.hass, tts_output["token"]))
            ):
                # Send TTS only if we haven't already started streaming it in INTENT_PROGRESS.
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._stream_tts(stream),
                    f"{self.entity_id} {event.type}",
                )
        elif event.type == assist_pipeline.PipelineEventType.ERROR:
            # Pipeline error
            if event.data:
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._client.write_event(
                        Error(
                            text=event.data["message"], code=event.data["code"]
                        ).event()
                    ),
                    f"{self.entity_id} {event.type}",
                )