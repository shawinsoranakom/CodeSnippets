async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""
        if user_input is not None:
            serial = user_input[CONF_DEVICE]
            await self.async_set_unique_id(serial, raise_on_progress=False)
            device_without_label = self._discovered_devices[serial]
            device = await self._async_try_connect(
                device_without_label.ip_addr, raise_on_progress=False
            )
            if not device:
                return self.async_abort(reason="cannot_connect")
            return self._async_create_entry_from_device(device)

        configured_serials: set[str] = set()
        configured_hosts: set[str] = set()
        for entry in self._async_current_entries():
            if entry.unique_id and not async_entry_is_legacy(entry):
                configured_serials.add(entry.unique_id)
                configured_hosts.add(entry.data[CONF_HOST])
        self._discovered_devices = {
            # device.mac_addr is not the mac_address, its the serial number
            device.mac_addr: device
            for device in await async_discover_devices(self.hass)
        }
        devices_name = {
            serial: f"{serial} ({device.ip_addr})"
            for serial, device in self._discovered_devices.items()
            if serial not in configured_serials
            and device.ip_addr not in configured_hosts
        }
        # Check if there is at least one device
        if not devices_name:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )