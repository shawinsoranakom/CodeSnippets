async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if self._async_in_progress():
            return self.async_abort(reason="already_in_progress")
        ports = await usb.async_scan_serial_ports(self.hass)
        existing_devices = [
            entry.data[CONF_DEVICE] for entry in self._async_current_entries()
        ]
        port_map = {
            usb.human_readable_device_name(
                port.device,
                port.serial_number,
                port.manufacturer,
                port.description,
                port.vid if isinstance(port, usb.USBDevice) else None,
                port.pid if isinstance(port, usb.USBDevice) else None,
            ): port
            for port in ports
            if port.device not in existing_devices
        }
        if not port_map:
            return self.async_abort(reason="no_devices_found")

        errors = {}
        if user_input is not None and user_input.get(CONF_DEVICE, "").strip():
            port = port_map[user_input[CONF_DEVICE]]
            dev_path = port.device
            unique_id = _generate_unique_id(port)
            await self.async_set_unique_id(unique_id)
            try:
                await self._validate_device(dev_path)
            except TimeoutError:
                errors[CONF_DEVICE] = "timeout_connect"
            except RAVEnConnectionError:
                errors[CONF_DEVICE] = "cannot_connect"
            else:
                return await self.async_step_meters()

        schema = vol.Schema({vol.Required(CONF_DEVICE): vol.In(list(port_map))})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)