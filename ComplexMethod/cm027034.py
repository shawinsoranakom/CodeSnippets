async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(self.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_confirm()

        current_addresses = self._async_current_ids(include_ignore=False)
        candidates = set()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses or not _is_supported(discovery_info):
                continue
            candidates.add(address)

        data = await async_get_manufacturer_data(candidates)
        for address, mfg_data in data.items():
            if mfg_data.product_type not in _SUPPORTED_PRODUCT_TYPES:
                continue
            self.devices[address] = PRODUCT_NAMES[mfg_data.product_type]

        # Keep selection sorted by address to ensure stable tests
        self.devices = dict(sorted(self.devices.items(), key=lambda x: x[0]))

        if not self.devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(self.devices),
                },
            ),
        )