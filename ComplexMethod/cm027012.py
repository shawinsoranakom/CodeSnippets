async def _async_set_info_from_discovery(
        self, discovery_info: SsdpServiceInfo, abort_if_configured: bool = True
    ) -> None:
        """Set information required for a config entry from the SSDP discovery."""
        LOGGER.debug(
            "_async_set_info_from_discovery: location: %s, UDN: %s",
            discovery_info.ssdp_location,
            discovery_info.ssdp_udn,
        )

        if not self._location:
            self._location = discovery_info.ssdp_location
            assert isinstance(self._location, str)

        self._udn = discovery_info.ssdp_udn
        await self.async_set_unique_id(self._udn, raise_on_progress=abort_if_configured)

        self._device_type = discovery_info.ssdp_nt or discovery_info.ssdp_st
        self._name = (
            discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME)
            or urlparse(self._location).hostname
            or DEFAULT_NAME
        )

        if host := discovery_info.ssdp_headers.get("_host"):
            self._mac = await _async_get_mac_address(self.hass, host)

        if abort_if_configured:
            # Abort if already configured, but update the last-known location
            updates = {CONF_URL: self._location}
            # Set the MAC address for older entries
            if self._mac:
                updates[CONF_MAC] = self._mac
            self._abort_if_unique_id_configured(updates=updates, reload_on_update=False)