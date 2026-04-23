def __init__(
        self,
        client: AsyncElevenLabs,
        model: Model,
        voices: list[ElevenLabsVoice],
        default_voice_id: str,
        entry_id: str,
        voice_settings: VoiceSettings,
    ) -> None:
        """Init ElevenLabs TTS service."""
        self._client = client
        self._model = model
        self._default_voice_id = default_voice_id
        self._voices = sorted(
            (Voice(v.voice_id, v.name) for v in voices if v.name),
            key=lambda v: v.name,
        )
        # Default voice first
        voice_indices = [
            idx for idx, v in enumerate(self._voices) if v.voice_id == default_voice_id
        ]
        if voice_indices:
            self._voices.insert(0, self._voices.pop(voice_indices[0]))
        self._voice_settings = voice_settings

        # Entity attributes
        self._attr_unique_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            manufacturer="ElevenLabs",
            model=model.name,
            name="ElevenLabs",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._attr_supported_languages = [
            lang.language_id for lang in self._model.languages or []
        ]
        # Use the first supported language as the default if available
        self._attr_default_language = (
            self._attr_supported_languages[0]
            if self._attr_supported_languages
            else "en"
        )