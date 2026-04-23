async def async_update_device_trackers(self, now=None) -> bool:
        """Update Netgear devices."""
        new_device = False
        ntg_devices = await self.async_get_attached_devices()
        now = dt_util.utcnow()

        if ntg_devices is None:
            return new_device

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Netgear scan result: \n%s", ntg_devices)

        for ntg_device in ntg_devices:
            if ntg_device.mac is None:
                continue

            device_mac = dr.format_mac(ntg_device.mac)

            if not self.devices.get(device_mac):
                new_device = True

            # ntg_device is a namedtuple from the collections module that needs conversion to a dict through ._asdict method
            self.devices[device_mac] = ntg_device._asdict()
            self.devices[device_mac]["mac"] = device_mac
            self.devices[device_mac]["last_seen"] = now

        for device in self.devices.values():
            device["active"] = now - device["last_seen"] <= self._consider_home
            if not device["active"]:
                device["link_rate"] = None
                device["signal"] = None
                device["ip"] = None
                device["ssid"] = None
                device["conn_ap_mac"] = None

        if new_device:
            _LOGGER.debug("Netgear tracker: new device found")

        return new_device