def on_pipeline_event(self, event: PipelineEvent) -> None:
        """Set state based on pipeline stage."""
        if event.type == PipelineEventType.STT_END:
            if (self._tones & Tones.PROCESSING) == Tones.PROCESSING:
                self._processing_tone_done.clear()
                self.config_entry.async_create_background_task(
                    self.hass, self._play_tone(Tones.PROCESSING), "voip_process_tone"
                )
        elif event.type == PipelineEventType.TTS_END:
            # Send TTS audio to caller over RTP
            if (
                event.data
                and (tts_output := event.data["tts_output"])
                and (stream := tts.async_get_stream(self.hass, tts_output["token"]))
            ):
                self.config_entry.async_create_background_task(
                    self.hass,
                    self._send_tts(tts_stream=stream),
                    "voip_pipeline_tts",
                )
            else:
                # Empty TTS response
                _LOGGER.debug("Empty TTS response")
                self._tts_done.set()
        elif event.type == PipelineEventType.ERROR:
            # Play error tone instead of wait for TTS when pipeline is finished.
            self._pipeline_had_error = True
            _LOGGER.warning(event)