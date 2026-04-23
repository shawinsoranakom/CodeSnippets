async def _async_try_fetch_device_info(self) -> ConfigFlowResult:
        """Try to fetch device info and return any errors."""
        response: str | None
        if self._noise_required:
            # If we already know we need encryption, don't try to fetch device info
            # without encryption.
            response = ERROR_REQUIRES_ENCRYPTION_KEY
        else:
            # After 2024.08, stop trying to fetch device info without encryption
            # so we can avoid probe requests to check for password. At this point
            # most devices should announce encryption support and password is
            # deprecated and can be discovered by trying to connect only after they
            # interact with the flow since it is expected to be a rare case.
            response = await self.fetch_device_info()

        if response == ERROR_REQUIRES_ENCRYPTION_KEY:
            if not self._device_name and not self._noise_psk:
                # If device name is not set we can send a zero noise psk
                # to get the device name which will allow us to populate
                # the device name and hopefully get the encryption key
                # from the dashboard.
                self._noise_psk = ZERO_NOISE_PSK
                response = await self.fetch_device_info()
                self._noise_psk = None

            # Try to retrieve an existing key from dashboard or storage.
            if (
                self._device_name
                and await self._retrieve_encryption_key_from_dashboard()
            ) or (
                self._device_mac and await self._retrieve_encryption_key_from_storage()
            ):
                response = await self.fetch_device_info()

            # If the fetched key is invalid, unset it again.
            if response == ERROR_INVALID_ENCRYPTION_KEY:
                self._noise_psk = None
                response = ERROR_REQUIRES_ENCRYPTION_KEY

        if response == ERROR_REQUIRES_ENCRYPTION_KEY:
            return await self.async_step_encryption_key()
        if response is not None:
            return await self._async_step_user_base(error=response)
        return await self._async_authenticate_or_add()