async def _send_tts(
        self,
        tts_stream: tts.ResultStream,
        wait_for_tone: bool = True,
    ) -> None:
        """Send TTS audio to caller via RTP."""
        try:
            if self.transport is None:
                return  # not connected

            data = b"".join([chunk async for chunk in tts_stream.async_stream_result()])

            if tts_stream.extension != "wav":
                raise ValueError(
                    f"Only TTS WAV audio can be streamed, got {tts_stream.extension}"
                )

            if wait_for_tone and ((self._tones & Tones.PROCESSING) == Tones.PROCESSING):
                # Don't overlap TTS and processing beep
                _LOGGER.debug("Waiting for processing tone")
                await self._processing_tone_done.wait()

            with io.BytesIO(data) as wav_io:
                with wave.open(wav_io, "rb") as wav_file:
                    sample_rate = wav_file.getframerate()
                    sample_width = wav_file.getsampwidth()
                    sample_channels = wav_file.getnchannels()

                    if (
                        (sample_rate != RATE)
                        or (sample_width != WIDTH)
                        or (sample_channels != CHANNELS)
                    ):
                        raise ValueError(
                            f"Expected rate/width/channels as {RATE}/{WIDTH}/{CHANNELS},"
                            f" got {sample_rate}/{sample_width}/{sample_channels}"
                        )

                audio_bytes = wav_file.readframes(wav_file.getnframes())

            _LOGGER.debug("Sending %s byte(s) of audio", len(audio_bytes))

            # Time out 1 second after TTS audio should be finished
            tts_samples = len(audio_bytes) / (WIDTH * CHANNELS)
            tts_seconds = tts_samples / RATE

            async with asyncio.timeout(tts_seconds + self._tts_extra_timeout):
                # TTS audio is 16Khz 16-bit mono
                await self._async_send_audio(audio_bytes)
        except TimeoutError:
            _LOGGER.warning("TTS timeout")
            raise
        finally:
            # Update satellite state
            self.tts_response_finished()

            # Signal pipeline to restart
            self._tts_done.set()