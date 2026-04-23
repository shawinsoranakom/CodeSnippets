async def _async_next_target(
        self,
    ) -> tuple[AnthropicConfigEntry, ConfigSubentry, str] | None:
        """Return the next deprecated subentry target."""
        if self._subentry_iter is None:
            self._subentry_iter = self._iter_deprecated_subentries()

        while True:
            try:
                entry_id, subentry_id = next(self._subentry_iter)
            except StopIteration:
                return None

            # Verify that the entry/subentry still exists and the model is still
            # deprecated. This may have changed since we started the repair flow.
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue

            subentry = entry.subentries.get(subentry_id)
            if subentry is None:
                continue

            model = subentry.data.get(CONF_CHAT_MODEL)
            if not model or model not in DEPRECATED_MODELS:
                continue

            self._current_entry_id = entry_id
            self._current_subentry_id = subentry_id
            return entry, subentry, model