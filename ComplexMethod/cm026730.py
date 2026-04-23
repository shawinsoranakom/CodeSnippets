async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Process an audio stream to STT service."""
        _LOGGER.debug(
            "Processing audio stream for STT: model=%s, language=%s, format=%s, codec=%s, sample_rate=%s, channels=%s, bit_rate=%s",
            self._stt_model,
            metadata.language,
            metadata.format,
            metadata.codec,
            metadata.sample_rate,
            metadata.channel,
            metadata.bit_rate,
        )

        if self._auto_detect_language:
            lang_code = None
        else:
            language = metadata.language
            if language.lower() not in [lang.lower() for lang in STT_LANGUAGES]:
                _LOGGER.warning("Unsupported language: %s", language)
                return stt.SpeechResult(None, SpeechResultState.ERROR)
            lang_code = language.split("-")[0]

        raw_pcm_compatible = (
            metadata.codec == AudioCodecs.PCM
            and metadata.sample_rate == AudioSampleRates.SAMPLERATE_16000
            and metadata.channel == AudioChannels.CHANNEL_MONO
            and metadata.bit_rate == AudioBitRates.BITRATE_16
        )
        if raw_pcm_compatible:
            file_format = "pcm_s16le_16"
        elif metadata.codec == AudioCodecs.PCM:
            _LOGGER.warning("PCM input does not meet expected raw format requirements")
            return stt.SpeechResult(None, SpeechResultState.ERROR)
        else:
            file_format = "other"

        audio = b""
        async for chunk in stream:
            audio += chunk

        _LOGGER.debug("Finished reading audio stream, total size: %d bytes", len(audio))
        if not audio:
            _LOGGER.warning("No audio received in stream")
            return stt.SpeechResult(None, SpeechResultState.ERROR)

        lang_display = lang_code or "auto-detected"

        _LOGGER.debug(
            "Transcribing audio (%s), format: %s, size: %d bytes",
            lang_display,
            file_format,
            len(audio),
        )

        try:
            kwargs: dict[str, Any] = {
                "file": BytesIO(audio),
                "file_format": file_format,
                "model_id": self._stt_model,
                "tag_audio_events": False,
                "num_speakers": 1,
                "diarize": False,
            }
            if lang_code is not None:
                kwargs["language_code"] = lang_code
            response = await self._client.speech_to_text.convert(**kwargs)
        except ApiError as exc:
            _LOGGER.error("Error during processing of STT request: %s", exc)
            return stt.SpeechResult(None, SpeechResultState.ERROR)

        text = response.text or ""
        detected_lang_code = response.language_code or "?"
        detected_lang_prob = response.language_probability or "?"

        _LOGGER.debug(
            "Transcribed text is in language %s (probability %s): %s",
            detected_lang_code,
            detected_lang_prob,
            text,
        )

        return stt.SpeechResult(text, SpeechResultState.SUCCESS)