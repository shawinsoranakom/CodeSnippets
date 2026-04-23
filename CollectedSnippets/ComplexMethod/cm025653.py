async def async_step_usb_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set up a Crownstone USB dongle."""
        list_of_ports = [
            p
            for p in await usb.async_scan_serial_ports(self.hass)
            if isinstance(p, usb.USBDevice)
        ]
        if self.flow_type == CONFIG_FLOW:
            ports_as_string = list_ports_as_str(list_of_ports)
        else:
            ports_as_string = list_ports_as_str(list_of_ports, False)

        if user_input is not None:
            selection = user_input[CONF_USB_PATH]

            if selection == DONT_USE_USB:
                return self.create_entry_callback()
            if selection == MANUAL_PATH:
                return await self.async_step_usb_manual_config()
            if selection != REFRESH_LIST:
                if self.flow_type == OPTIONS_FLOW:
                    index = ports_as_string.index(selection)
                else:
                    index = ports_as_string.index(selection) - 1

                selected_port = list_of_ports[index]
                self.usb_path = selected_port.device
                return await self.async_step_usb_sphere_config()

        return self.async_show_form(
            step_id="usb_config",
            data_schema=vol.Schema(
                {vol.Required(CONF_USB_PATH): vol.In(ports_as_string)}
            ),
        )