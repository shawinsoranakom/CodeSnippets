async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Migrate to the new version."""

        async def google_connected() -> bool:
            """Return True if our user is preset in the google_assistant store."""
            # If we don't have a user, we can't be connected to Google
            if not (cur_username := old_data.get(PREF_USERNAME)):
                return False

            # If our user is in the Google store, we're connected
            return cur_username in await async_get_google_assistant_users(self.hass)

        if old_major_version == 1:
            if old_minor_version < 2:
                old_data.setdefault(PREF_ALEXA_SETTINGS_VERSION, 1)
                old_data.setdefault(PREF_GOOGLE_SETTINGS_VERSION, 1)
            if old_minor_version < 3:
                # Import settings from the google_assistant store which was previously
                # shared between the cloud integration and manually configured Google
                # assistant.
                # In HA Core 2024.9, remove the import and also remove the Google
                # assistant store if it's not been migrated by manual Google assistant
                old_data.setdefault(PREF_GOOGLE_CONNECTED, await google_connected())
            if old_minor_version < 4:
                # Update the default TTS voice to the new default.
                # The default tts voice is a tuple.
                # The first item is the language, the second item used to be gender.
                # The new second item is the voice name.
                default_tts_voice = old_data.get(PREF_TTS_DEFAULT_VOICE)
                if default_tts_voice and (voice_item_two := default_tts_voice[1]) in (
                    Gender.FEMALE,
                    Gender.MALE,
                ):
                    language: str = default_tts_voice[0]
                    if voice := MAP_VOICE.get((language, voice_item_two)):
                        old_data[PREF_TTS_DEFAULT_VOICE] = (
                            language,
                            voice,
                        )
                    else:
                        old_data[PREF_TTS_DEFAULT_VOICE] = DEFAULT_TTS_DEFAULT_VOICE

        return old_data