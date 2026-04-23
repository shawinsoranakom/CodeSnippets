async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""
        if user_input is not None:
            device = self._discovered_devices[user_input[CONF_DEVICE]]
            await self.async_set_unique_id(device.mac_address, raise_on_progress=False)
            bulb = wizlight(device.ip_address)
            try:
                bulbtype = await bulb.get_bulbtype()
            except WIZ_CONNECT_EXCEPTIONS:
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title=name_from_bulb_type_and_mac(bulbtype, device.mac_address),
                data={CONF_HOST: device.ip_address},
            )

        current_unique_ids = self._async_current_ids(include_ignore=False)
        current_hosts = {
            entry.data[CONF_HOST]
            for entry in self._async_current_entries(include_ignore=False)
        }
        discovered_devices = await async_discover_devices(
            self.hass, DISCOVER_SCAN_TIMEOUT
        )
        self._discovered_devices = {
            device.mac_address: device for device in discovered_devices
        }
        devices_name = {
            mac: f"{DEFAULT_NAME} {_short_mac(mac)} ({device.ip_address})"
            for mac, device in self._discovered_devices.items()
            if mac not in current_unique_ids and device.ip_address not in current_hosts
        }
        # Check if there is at least one device
        if not devices_name:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )