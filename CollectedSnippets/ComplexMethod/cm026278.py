def _async_get_human_readable_name(self) -> str:
        """Return a human readable name for the entry."""
        entry: ConfigEntry | None = None
        if self.source == SOURCE_REAUTH:
            entry = self._reauth_entry
        elif self.source == SOURCE_RECONFIGURE:
            entry = self._reconfig_entry
        friendly_name = self._name
        device_name = self._device_name
        if (
            device_name
            and friendly_name in (DEFAULT_NAME, device_name)
            and entry
            and entry.title != friendly_name
        ):
            friendly_name = entry.title
        if not device_name or friendly_name == device_name:
            return friendly_name
        return f"{friendly_name} ({device_name})"