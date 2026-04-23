def _async_create_or_update_entry_from_device(
        self, device: Device, *, camera_data: dict | None = None
    ) -> ConfigFlowResult:
        """Create a config entry from a smart device."""
        entry = None
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
        elif self.source == SOURCE_REAUTH:
            entry = self._get_reauth_entry()

        if not entry:
            self._abort_if_unique_id_configured(updates={CONF_HOST: device.host})

        data: dict[str, Any] = {
            CONF_HOST: device.host,
            CONF_ALIAS: device.alias,
            CONF_MODEL: device.model,
            CONF_CONNECTION_PARAMETERS: device.config.connection_type.to_dict(),
            CONF_USES_HTTP: device.config.uses_http,
        }
        if camera_data is not None:
            data[CONF_LIVE_VIEW] = camera_data[CONF_LIVE_VIEW]
            if camera_creds := camera_data.get(CONF_CAMERA_CREDENTIALS):
                data[CONF_CAMERA_CREDENTIALS] = camera_creds

        if device.config.aes_keys:
            data[CONF_AES_KEYS] = device.config.aes_keys

        # This is only ever called after a successful device update so we know that
        # the credential_hash is correct and should be saved.
        if device.credentials_hash:
            data[CONF_CREDENTIALS_HASH] = device.credentials_hash
        if port := device.config.port_override:
            data[CONF_PORT] = port

        if not entry:
            return self.async_create_entry(
                title=f"{device.alias} {device.model}",
                data=data,
            )

        return self.async_update_reload_and_abort(entry, data=data)