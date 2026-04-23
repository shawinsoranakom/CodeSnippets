async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose advanced options."""
        hk_options = self.hk_options
        show_advanced_options = self.show_advanced_options
        bridge_mode = hk_options[CONF_HOMEKIT_MODE] == HOMEKIT_MODE_BRIDGE

        if not show_advanced_options or user_input is not None or not bridge_mode:
            if user_input:
                hk_options.update(user_input)
                if show_advanced_options and bridge_mode:
                    hk_options[CONF_DEVICES] = user_input[CONF_DEVICES]

            hk_options.pop(CONF_DOMAINS, None)
            hk_options.pop(CONF_ENTITIES, None)
            hk_options.pop(CONF_INCLUDE_EXCLUDE_MODE, None)
            return self.async_create_entry(title="", data=self.hk_options)

        all_supported_devices = await _async_get_supported_devices(self.hass)
        # Strip out devices that no longer exist to prevent error in the UI
        devices = [
            device_id
            for device_id in self.hk_options.get(CONF_DEVICES, [])
            if device_id in all_supported_devices
        ]
        return self.async_show_form(
            step_id="advanced",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_DEVICES, default=devices): cv.multi_select(
                        all_supported_devices
                    )
                }
            ),
        )