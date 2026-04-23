def async_satellite_config_updated(
        self, config: AssistSatelliteConfiguration
    ) -> None:
        """Update options with available wake words."""
        if (not config.available_wake_words) or (config.max_active_wake_words < 1):
            # No wake words
            self._wake_words.clear()
            self._attr_current_option = NO_WAKE_WORD
            self._attr_options = [NO_WAKE_WORD]
            self._entry_data.assist_satellite_wake_words.pop(
                self._wake_word_index, None
            )
            self.async_write_ha_state()
            return

        self._wake_words = {w.wake_word: w.id for w in config.available_wake_words}
        self._attr_options = [NO_WAKE_WORD, *sorted(self._wake_words)]

        option = self._attr_current_option

        if (
            (self._wake_word_index == 0)
            and (len(config.active_wake_words) == 1)
            and (option in (None, NO_WAKE_WORD))
        ):
            option = next(
                (
                    wake_word
                    for wake_word, wake_word_id in self._wake_words.items()
                    if wake_word_id == config.active_wake_words[0]
                ),
                None,
            )

        if (
            (option is None)
            or ((wake_word_id := self._wake_words.get(option)) is None)
            or (wake_word_id not in config.active_wake_words)
        ):
            option = NO_WAKE_WORD

        self._attr_current_option = option
        self.async_write_ha_state()

        # Keep entry data in sync
        if wake_word_id := self._wake_words.get(option):
            self._entry_data.assist_satellite_wake_words[self._wake_word_index] = (
                wake_word_id
            )
        else:
            self._entry_data.assist_satellite_wake_words.pop(
                self._wake_word_index, None
            )