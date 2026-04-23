async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""
        if user_input is not None:
            mac = user_input[CONF_DEVICE]
            await self.async_set_unique_id(mac, raise_on_progress=False)
            self._discovered_device = self._discovered_devices[mac]
            self.host = self._discovered_device.host
            credentials = await get_credentials(self.hass)

            try:
                device = await self._async_try_connect(
                    self._discovered_device, credentials
                )
            except AuthenticationError:
                return await self.async_step_user_auth_confirm()
            except KasaException:
                return self.async_abort(reason="cannot_connect")

            if self._async_supports_camera_credentials(device):
                return await self.async_step_camera_auth_confirm()

            return self._async_create_or_update_entry_from_device(device)

        configured_devices = {
            entry.unique_id for entry in self._async_current_entries()
        }
        self._discovered_devices = await async_discover_devices(self.hass)
        devices_name = {
            formatted_mac: (
                f"{device.alias or mac_alias(device.mac)} {device.model} ({device.host}) {formatted_mac}"
            )
            for formatted_mac, device in self._discovered_devices.items()
            if formatted_mac not in configured_devices
        }
        # Check if there is at least one device
        if not devices_name:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(devices_name)}),
        )