async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if mac := user_input[CONF_DEVICE]:
                await self.async_set_unique_id(mac, raise_on_progress=False)
                self._discovered_device = self._discovered_devices[mac]
                return await self.async_step_discovered_connection()
            return await self.async_step_manual_connection()

        current_unique_ids = self._async_current_ids(include_ignore=False)
        current_hosts = {
            hostname_from_url(entry.data[CONF_HOST])
            for entry in self._async_current_entries(include_ignore=False)
        }
        discovered_devices = await async_discover_devices(
            self.hass, DISCOVER_SCAN_TIMEOUT
        )
        self._discovered_devices = {
            dr.format_mac(device.mac_address): device for device in discovered_devices
        }
        devices_name: dict[str | None, str] = {
            mac: f"{_short_mac(device.mac_address)} ({device.ip_address})"
            for mac, device in self._discovered_devices.items()
            if mac not in current_unique_ids and device.ip_address not in current_hosts
        }
        if not devices_name:
            return await self.async_step_manual_connection()
        devices_name[None] = "Manual Entry"
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )