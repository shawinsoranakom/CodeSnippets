async def async_step_device(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle WS-Discovery.

        Let user choose between discovered devices and manual configuration.
        If no device is found allow user to manually input configuration.
        """
        if user_input:
            if user_input[CONF_HOST] == CONF_MANUAL_INPUT:
                return await self.async_step_configure()

            for device in self.devices:
                if device[CONF_HOST] == user_input[CONF_HOST]:
                    self.device_id = device[CONF_DEVICE_ID]
                    self.onvif_config = {
                        CONF_NAME: device[CONF_NAME],
                        CONF_HOST: device[CONF_HOST],
                        CONF_PORT: device[CONF_PORT],
                    }
                    return await self.async_step_configure()

        discovery = await async_discovery(self.hass)
        for device in discovery:
            configured = any(
                entry.unique_id == device[CONF_DEVICE_ID]
                for entry in self._async_current_entries()
            )

            if not configured:
                self.devices.append(device)

        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("Discovered ONVIF devices %s", pformat(self.devices))

        if self.devices:
            devices = {CONF_MANUAL_INPUT: CONF_MANUAL_INPUT}
            for device in self.devices:
                description = f"{device[CONF_NAME]} ({device[CONF_HOST]})"
                if hardware := device[CONF_HARDWARE]:
                    description += f" [{hardware}]"
                devices[device[CONF_HOST]] = description

            return self.async_show_form(
                step_id="device",
                data_schema=vol.Schema({vol.Optional(CONF_HOST): vol.In(devices)}),
            )

        return await self.async_step_configure()