async def _handle_dynamic_encryption_key(
        self, device_info: EsphomeDeviceInfo
    ) -> None:
        """Handle dynamic encryption keys.

        If a device reports it supports encryption, but we connected without a key,
        we need to generate and store one.
        """
        noise_psk: str | None = self.entry.data.get(CONF_NOISE_PSK)
        if noise_psk:
            # we're already connected with a noise PSK - nothing to do
            return

        if not device_info.api_encryption_supported:
            # device does not support encryption - nothing to do
            return

        # Connected to device without key and the device supports encryption
        storage = await async_get_encryption_key_storage(self.hass)

        # First check if we have a key in storage for this device
        from_storage: bool = False
        if self.entry.unique_id and (
            stored_key := await storage.async_get_key(self.entry.unique_id)
        ):
            _LOGGER.debug(
                "Retrieved encryption key from storage for device %s",
                self.entry.unique_id,
            )
            # Use the stored key
            new_key = stored_key.encode()
            new_key_str = stored_key
            from_storage = True
        else:
            # No stored key found, generate a new one
            _LOGGER.debug(
                "Generating new encryption key for device %s", self.entry.unique_id
            )
            new_key = base64.b64encode(secrets.token_bytes(32))
            new_key_str = new_key.decode()

        try:
            # Store the key on the device using the existing connection
            result = await self.cli.noise_encryption_set_key(new_key)
        except APIConnectionError as ex:
            _LOGGER.error(
                "Connection error while storing encryption key for device %s (%s): %s",
                self.entry.data.get(CONF_DEVICE_NAME, self.host),
                self.entry.unique_id,
                ex,
            )
            return
        else:
            if not result:
                _LOGGER.error(
                    "Failed to set dynamic encryption key on device %s (%s)",
                    self.entry.data.get(CONF_DEVICE_NAME, self.host),
                    self.entry.unique_id,
                )
                return

        # Key stored successfully on device
        assert self.entry.unique_id is not None

        # Only store in storage if it was newly generated
        if not from_storage:
            await storage.async_store_key(self.entry.unique_id, new_key_str)

        # Always update config entry
        self.hass.config_entries.async_update_entry(
            self.entry,
            data={**self.entry.data, CONF_NOISE_PSK: new_key_str},
        )

        if from_storage:
            _LOGGER.info(
                "Set encryption key from storage on device %s (%s)",
                self.entry.data.get(CONF_DEVICE_NAME, self.host),
                self.entry.unique_id,
            )
        else:
            _LOGGER.info(
                "Generated and stored encryption key for device %s (%s)",
                self.entry.data.get(CONF_DEVICE_NAME, self.host),
                self.entry.unique_id,
            )