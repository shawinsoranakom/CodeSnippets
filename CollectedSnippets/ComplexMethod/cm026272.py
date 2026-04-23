async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a flow initialized by a reauth event."""
        self._reauth_entry = self._get_reauth_entry()
        self._host = entry_data[CONF_HOST]
        self._port = entry_data[CONF_PORT]
        self._password = entry_data[CONF_PASSWORD]
        self._device_name = entry_data.get(CONF_DEVICE_NAME)
        self._name = self._reauth_entry.title

        # Device without encryption allows fetching device info. We can then check
        # if the device is no longer using a password. If we did try with a password,
        # we know setting password to empty will allow us to authenticate.
        error = await self.fetch_device_info()
        if (
            error is None
            and self._password
            and self._device_info
            and not self._device_info.uses_password
        ):
            self._password = ""
            return await self._async_authenticate_or_add()

        if error == ERROR_INVALID_PASSWORD_AUTH or (
            error is None and self._device_info and self._device_info.uses_password
        ):
            return await self.async_step_authenticate()

        if error is None and entry_data.get(CONF_NOISE_PSK):
            # Device was configured with encryption but now connects without it.
            # Check if it's the same device before offering to remove encryption.
            if self._reauth_entry.unique_id and self._device_mac:
                expected_mac = format_mac(self._reauth_entry.unique_id)
                actual_mac = format_mac(self._device_mac)
                if expected_mac != actual_mac:
                    # Different device at the same IP - do not offer to remove encryption
                    return self._async_abort_wrong_device(
                        self._reauth_entry, expected_mac, actual_mac
                    )
            return await self.async_step_reauth_encryption_removed_confirm()
        return await self.async_step_reauth_confirm()