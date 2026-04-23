async def async_step_name_conflict_migrate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle migration of existing entry."""
        assert self._entry_with_name_conflict is not None
        assert self._entry_with_name_conflict.unique_id is not None
        assert self.unique_id is not None
        assert self._device_name is not None
        assert self._host is not None
        old_mac = format_mac(self._entry_with_name_conflict.unique_id)
        new_mac = format_mac(self.unique_id)
        entry_id = self._entry_with_name_conflict.entry_id
        self.hass.config_entries.async_update_entry(
            self._entry_with_name_conflict,
            data={
                **self._entry_with_name_conflict.data,
                CONF_HOST: self._host,
                CONF_PORT: self._port or DEFAULT_PORT,
                CONF_PASSWORD: self._password or "",
                CONF_NOISE_PSK: self._noise_psk or "",
            },
        )
        await async_replace_device(self.hass, entry_id, old_mac, new_mac)
        self.hass.config_entries.async_schedule_reload(entry_id)
        return self.async_abort(
            reason="name_conflict_migrated",
            description_placeholders={
                "existing_mac": old_mac,
                "mac": new_mac,
                "name": self._device_name,
            },
        )