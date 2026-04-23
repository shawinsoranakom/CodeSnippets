async def _async_get_tts_audio(
        self,
        message: str,
        language: str,
        options: dict[str, Any],
    ) -> TtsAudioType:
        """Load TTS from Google Cloud."""
        try:
            options = self._options_schema(options)
        except vol.Invalid as err:
            _LOGGER.error("Error: %s when validating options: %s", err, options)
            return None, None

        encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding[
            options[CONF_ENCODING]
        ]  # type: ignore[misc]
        gender: texttospeech.SsmlVoiceGender | None = texttospeech.SsmlVoiceGender[
            options[CONF_GENDER]
        ]  # type: ignore[misc]
        voice = options[CONF_VOICE]
        if voice:
            gender = None
            if not voice.startswith(language):
                language = voice[:5]

        request = texttospeech.SynthesizeSpeechRequest(
            input=texttospeech.SynthesisInput(**{options[CONF_TEXT_TYPE]: message}),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language,
                ssml_gender=gender,
                name=voice,
            ),
            # Avoid: "This voice does not support speaking rate or pitch parameters at this time."
            # by not specifying the fields unless they differ from the defaults
            audio_config=texttospeech.AudioConfig(
                audio_encoding=encoding,
                speaking_rate=(
                    options[CONF_SPEED]
                    if options[CONF_SPEED] != DEFAULT_SPEED
                    else None
                ),
                pitch=(
                    options[CONF_PITCH]
                    if options[CONF_PITCH] != DEFAULT_PITCH
                    else None
                ),
                volume_gain_db=(
                    options[CONF_GAIN] if options[CONF_GAIN] != DEFAULT_GAIN else None
                ),
                effects_profile_id=options[CONF_PROFILES],
            ),
        )

        response = await self._client.synthesize_speech(
            request,
            timeout=30,
            retry=AsyncRetry(initial=0.1, maximum=2.0, multiplier=2.0),
        )

        if encoding == texttospeech.AudioEncoding.MP3:
            extension = "mp3"
        elif encoding == texttospeech.AudioEncoding.OGG_OPUS:
            extension = "ogg"
        else:
            extension = "wav"

        return extension, response.audio_content