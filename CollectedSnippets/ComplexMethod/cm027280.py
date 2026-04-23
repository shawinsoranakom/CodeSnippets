async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            return await self._async_create_entry_internal(
                self._discovery_infos[address]
            )

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery_info in async_discovered_service_info(self.hass, True):
            address = discovery_info.address
            if (
                address in current_addresses
                or address in self._discovery_infos
                or discovery_info.name not in SUPPORTED_DEVICES
            ):
                continue
            self._discovery_infos[address] = discovery_info

        if not self._discovery_infos:
            return self.async_abort(reason="no_devices_found")

        addresses = {info.address: info.name for info in self._discovery_infos.values()}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(addresses)}),
        )