async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        assert self._entry_data.device_info is not None
        feature_flags = (
            self._entry_data.device_info.voice_assistant_feature_flags_compat(
                self._entry_data.api_version
            )
        )
        if feature_flags & VoiceAssistantFeature.API_AUDIO:
            # TCP audio
            self.async_on_remove(
                self.cli.subscribe_voice_assistant(
                    handle_start=self.handle_pipeline_start,
                    handle_stop=self.handle_pipeline_stop,
                    handle_audio=self.handle_audio,
                    handle_announcement_finished=self.handle_announcement_finished,
                )
            )
        else:
            # UDP audio
            self.async_on_remove(
                self.cli.subscribe_voice_assistant(
                    handle_start=self.handle_pipeline_start,
                    handle_stop=self.handle_pipeline_stop,
                    handle_announcement_finished=self.handle_announcement_finished,
                )
            )

        if feature_flags & VoiceAssistantFeature.TIMERS:
            # Device supports timers
            assert (self.registry_entry is not None) and (
                self.registry_entry.device_id is not None
            )
            self.async_on_remove(
                async_register_timer_handler(
                    self.hass, self.registry_entry.device_id, self.handle_timer_event
                )
            )

        assert self._attr_supported_features is not None
        if feature_flags & VoiceAssistantFeature.ANNOUNCE:
            # Device supports announcements
            self._attr_supported_features |= (
                assist_satellite.AssistSatelliteEntityFeature.ANNOUNCE
            )

            # Block until config is retrieved.
            # If the device supports announcements, it will return a config.
            _LOGGER.debug("Waiting for satellite configuration")
            await self._update_satellite_config()

        if not (feature_flags & VoiceAssistantFeature.SPEAKER):
            # Will use media player for TTS/announcements
            self._update_tts_format()

        if feature_flags & VoiceAssistantFeature.START_CONVERSATION:
            self._attr_supported_features |= (
                assist_satellite.AssistSatelliteEntityFeature.START_CONVERSATION
            )

        # Update wake word select when config is updated
        self.async_on_remove(
            self._entry_data.async_register_assist_satellite_set_wake_words_callback(
                self.async_set_wake_words
            )
        )