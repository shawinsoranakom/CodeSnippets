async def _stream_tts(self, tts_result: tts.ResultStream) -> None:
        """Stream TTS WAV audio to satellite in chunks."""
        client = self._client
        if client is None:
            # Satellite disconnected, cannot stream
            return

        if tts_result.extension != "wav":
            raise ValueError(
                f"Cannot stream audio format to satellite: {tts_result.extension}"
            )

        # Track the total duration of TTS audio for response timeout
        total_seconds = 0.0
        start_time = time.monotonic()

        try:
            header_data = b""
            header_complete = False
            sample_rate: int | None = None
            sample_width: int | None = None
            sample_channels: int | None = None
            timestamp = 0

            async for data_chunk in tts_result.async_stream_result():
                if not header_complete:
                    # Accumulate data until we can parse the header and get
                    # sample rate, etc.
                    header_data += data_chunk
                    # Most WAVE headers are 44 bytes in length
                    if (len(header_data) >= 44) and (
                        audio_info := _try_parse_wav_header(header_data)
                    ):
                        # Overwrite chunk with audio after header
                        sample_rate, sample_width, sample_channels, data_chunk = (
                            audio_info
                        )
                        await client.write_event(
                            AudioStart(
                                rate=sample_rate,
                                width=sample_width,
                                channels=sample_channels,
                                timestamp=timestamp,
                            ).event()
                        )
                        header_complete = True

                        if not data_chunk:
                            # No audio after header
                            continue
                    else:
                        # Header is incomplete
                        continue

                # Streaming audio
                assert sample_rate is not None
                assert sample_width is not None
                assert sample_channels is not None

                data_chunk_idx = 0
                while data_chunk_idx < len(data_chunk):
                    audio_chunk = AudioChunk(
                        rate=sample_rate,
                        width=sample_width,
                        channels=sample_channels,
                        audio=data_chunk[
                            data_chunk_idx : data_chunk_idx + _AUDIO_CHUNK_BYTES
                        ],
                        timestamp=timestamp,
                    )

                    await client.write_event(audio_chunk.event())
                    timestamp += audio_chunk.milliseconds
                    total_seconds += audio_chunk.seconds
                    data_chunk_idx += _AUDIO_CHUNK_BYTES

            await client.write_event(AudioStop(timestamp=timestamp).event())
            _LOGGER.debug("TTS streaming complete")
        finally:
            send_duration = time.monotonic() - start_time
            timeout_seconds = max(0, total_seconds - send_duration + _TTS_TIMEOUT_EXTRA)
            self.config_entry.async_create_background_task(
                self.hass,
                self._tts_timeout(timeout_seconds, self._run_loop_id),
                name="wyoming TTS timeout",
            )