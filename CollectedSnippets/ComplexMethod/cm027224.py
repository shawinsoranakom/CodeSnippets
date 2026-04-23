async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] | None = {}
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

        if user_input is not None:
            port = port_map[user_input[CONF_DEVICE]]
            dev_path = port.device
            errors = await self.validate_device_errors(
                dev_path=dev_path, unique_id=_generate_unique_id(port)
            )
            if errors is None:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={CONF_DEVICE: dev_path},
                )
        user_input = user_input or {}
        schema = vol.Schema({vol.Required(CONF_DEVICE): vol.In(list(port_map))})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)