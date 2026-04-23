async def _stream_tts_audio(
        self,
        tts_result: tts.ResultStream,
        sample_rate: int = 16000,
        sample_width: int = 2,
        sample_channels: int = 1,
        samples_per_chunk: int = 512,
    ) -> None:
        """Stream TTS audio chunks to device via API or UDP."""
        self.cli.send_voice_assistant_event(
            VoiceAssistantEventType.VOICE_ASSISTANT_TTS_STREAM_START, {}
        )

        try:
            if not self._is_running:
                return

            if tts_result.extension != "wav":
                _LOGGER.error(
                    "Only WAV audio can be streamed, got %s", tts_result.extension
                )
                return

            data = b"".join([chunk async for chunk in tts_result.async_stream_result()])

            with io.BytesIO(data) as wav_io, wave.open(wav_io, "rb") as wav_file:
                if (
                    (wav_file.getframerate() != sample_rate)
                    or (wav_file.getsampwidth() != sample_width)
                    or (wav_file.getnchannels() != sample_channels)
                ):
                    _LOGGER.error("Can only stream 16Khz 16-bit mono WAV")
                    return

                _LOGGER.debug("Streaming %s audio samples", wav_file.getnframes())

                while self._is_running:
                    chunk = wav_file.readframes(samples_per_chunk)
                    if not chunk:
                        break

                    if self._udp_server is not None:
                        self._udp_server.send_audio_bytes(chunk)
                    else:
                        self.cli.send_voice_assistant_audio(chunk)

                    # Wait for 90% of the duration of the audio that was
                    # sent for it to be played.  This will overrun the
                    # device's buffer for very long audio, so using a media
                    # player is preferred.
                    samples_in_chunk = len(chunk) // (sample_width * sample_channels)
                    seconds_in_chunk = samples_in_chunk / sample_rate
                    await asyncio.sleep(seconds_in_chunk * 0.9)
        except asyncio.CancelledError:
            return  # Don't trigger state change
        finally:
            self.cli.send_voice_assistant_event(
                VoiceAssistantEventType.VOICE_ASSISTANT_TTS_STREAM_END, {}
            )

        # State change
        self.tts_response_finished()
        self._entry_data.async_set_assist_pipeline_state(False)