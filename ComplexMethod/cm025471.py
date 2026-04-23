async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""
        if user_input is not None:
            mac = user_input[CONF_DEVICE]
            await self.async_set_unique_id(mac, raise_on_progress=False)
            device = self._discovered_devices[mac]
            if not device.get(ATTR_MODEL_DESCRIPTION):
                with contextlib.suppress(*FLUX_LED_EXCEPTIONS):
                    device = await self._async_try_connect(device[ATTR_IPADDR], device)
            return self._async_create_entry_from_device(device)

        current_unique_ids = self._async_current_ids()
        current_hosts = {
            entry.data[CONF_HOST]
            for entry in self._async_current_entries(include_ignore=False)
        }
        discovered_devices = await async_discover_devices(
            self.hass, DISCOVER_SCAN_TIMEOUT
        )
        self._discovered_devices = {}
        for device in discovered_devices:
            mac_address = device[ATTR_ID]
            assert mac_address is not None
            self._discovered_devices[dr.format_mac(mac_address)] = device
        devices_name = {
            mac: f"{async_name_from_discovery(device)} ({device[ATTR_IPADDR]})"
            for mac, device in self._discovered_devices.items()
            if mac not in current_unique_ids
            and device[ATTR_IPADDR] not in current_hosts
        }
        # Check if there is at least one device
        if not devices_name:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )