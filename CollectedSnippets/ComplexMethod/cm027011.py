async def _async_connect(self) -> None:
        """Connect to a device to confirm it works and gather extra information.

        Updates this flow's unique ID to the device UDN if not already done.
        Raises ConnectError if something goes wrong.
        """
        LOGGER.debug("_async_connect: location: %s", self._location)
        assert self._location, "self._location has not been set before connect"

        domain_data = get_domain_data(self.hass)
        try:
            device = await domain_data.upnp_factory.async_create_device(self._location)
        except UpnpError as err:
            raise ConnectError("cannot_connect") from err

        if not DmrDevice.is_profile_device(device):
            raise ConnectError("not_dmr")

        device = find_device_of_type(device, DmrDevice.DEVICE_TYPES)

        if not self._udn:
            self._udn = device.udn
            await self.async_set_unique_id(self._udn)

        # Abort if already configured, but update the last-known location
        self._abort_if_unique_id_configured(
            updates={CONF_URL: self._location}, reload_on_update=False
        )

        if not self._device_type:
            self._device_type = device.device_type

        if not self._name:
            self._name = device.name

        if not self._mac and (host := urlparse(self._location).hostname):
            self._mac = await _async_get_mac_address(self.hass, host)