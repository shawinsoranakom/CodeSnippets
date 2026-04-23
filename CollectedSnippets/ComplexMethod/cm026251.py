async def on_connect_error(self, err: Exception) -> None:
        """Start reauth flow if appropriate connect error type."""
        if not isinstance(
            err,
            (
                EncryptionPlaintextAPIError,
                RequiresEncryptionAPIError,
                InvalidEncryptionKeyAPIError,
                InvalidAuthAPIError,
            ),
        ):
            return

        if isinstance(err, InvalidEncryptionKeyAPIError):
            if (
                (received_name := err.received_name)
                and (received_mac := err.received_mac)
                and (unique_id := self.entry.unique_id)
                and ":" in unique_id
            ):
                formatted_received_mac = format_mac(received_mac)
                formatted_expected_mac = format_mac(unique_id)
                if formatted_received_mac != formatted_expected_mac:
                    _LOGGER.error(
                        "Unexpected device found at %s; "
                        "expected `%s` with mac address `%s`, "
                        "found `%s` with mac address `%s`",
                        self.host,
                        self.entry.data.get(CONF_DEVICE_NAME),
                        formatted_expected_mac,
                        received_name,
                        formatted_received_mac,
                    )
                    # If the device comes back online, discovery
                    # will update the config entry with the new IP address
                    # and reload which will try again to connect to the device.
                    # In the mean time we stop the reconnect logic
                    # so we don't keep trying to connect to the wrong device.
                    if self.reconnect_logic:
                        await self.reconnect_logic.stop()
                    return
        await self._start_reauth_and_disconnect()