async def _async_reconfig_validated_connection(self) -> ConfigFlowResult:
        """Handle reconfigure validated connection."""
        assert self._reconfig_entry.unique_id is not None
        assert self._host is not None
        assert self._device_name is not None
        if not (
            unique_id_matches := (self.unique_id == self._reconfig_entry.unique_id)
        ):
            self._abort_unique_id_configured_with_details(
                updates={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_NOISE_PSK: self._noise_psk,
                }
            )
        for entry in self._async_current_entries(include_ignore=False):
            if (
                entry.entry_id != self._reconfig_entry.entry_id
                and entry.data.get(CONF_DEVICE_NAME) == self._device_name
            ):
                return self.async_abort(
                    reason="reconfigure_name_conflict",
                    description_placeholders={
                        "name": self._reconfig_entry.data[CONF_DEVICE_NAME],
                        "host": self._host,
                        "expected_mac": format_mac(self._reconfig_entry.unique_id),
                        "existing_title": entry.title,
                    },
                )
        if unique_id_matches:
            return self.async_update_reload_and_abort(
                self._reconfig_entry,
                data=self._reconfig_entry.data | self._async_make_config_data(),
            )
        if self._reconfig_entry.data.get(CONF_DEVICE_NAME) == self._device_name:
            self._entry_with_name_conflict = self._reconfig_entry
            return await self.async_step_name_conflict()
        return self._async_abort_wrong_device(
            self._reconfig_entry,
            format_mac(self._reconfig_entry.unique_id),
            format_mac(self.unique_id),
        )