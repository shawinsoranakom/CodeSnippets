async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            # Guard against the user selecting a device which has been configured by
            # another flow.
            self._abort_if_unique_id_configured()
            self._discovery_info = self._discovered_devices[address]
            return await self.async_step_associate()

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery in async_discovered_service_info(self.hass):
            if (
                discovery.address in current_addresses
                or discovery.address in self._discovered_devices
                or not device_filter(discovery.advertisement)
            ):
                continue
            self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: (
                            f"{service_info.name} ({service_info.address})"
                        )
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )