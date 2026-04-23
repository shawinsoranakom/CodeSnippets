async def _async_validate_mac_abort_configured(
        self, formatted_mac: str, host: str, port: int | None
    ) -> None:
        """Validate if the MAC address is already configured."""
        assert self.unique_id is not None
        if not (
            entry := self.hass.config_entries.async_entry_for_domain_unique_id(
                self.handler, formatted_mac
            )
        ):
            return
        if entry.source == SOURCE_IGNORE:
            # Don't call _fetch_device_info() for ignored entries
            raise AbortFlow("already_configured")
        configured_host: str | None = entry.data.get(CONF_HOST)
        configured_port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)
        # When port is None (from DHCP discovery), only compare hosts
        if configured_host == host and (port is None or configured_port == port):
            # Don't probe to verify the mac is correct since
            # the host matches (and port matches if provided).
            raise AbortFlow("already_configured")
        # If the entry is loaded and the device is currently connected,
        # don't update the host. This prevents transient mDNS announcements
        # (e.g., during WiFi mesh roaming) from overwriting a working connection.
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data.available:
            raise AbortFlow("already_configured")
        configured_psk: str | None = entry.data.get(CONF_NOISE_PSK)
        await self._fetch_device_info(host, port or configured_port, configured_psk)
        updates: dict[str, Any] = {}
        if self._device_mac == formatted_mac:
            updates[CONF_HOST] = host
            if port is not None:
                updates[CONF_PORT] = port
        self._abort_unique_id_configured_with_details(updates=updates)