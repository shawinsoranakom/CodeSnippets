async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""

        if user_input is not None:
            address = user_input[CONF_ADDRESS]

            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            return self._create_entry(address)

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery_info in async_discovered_service_info(
            self.hass, connectable=True
        ):
            if discovery_info.manufacturer_id == MANUFACTURER_ID and any(
                manufacturer_data.startswith(MANUFACTURER_DATA_START)
                for manufacturer_data in discovery_info.manufacturer_data.values()
            ):
                address = discovery_info.address
                if (
                    address not in current_addresses
                    and address not in self._discovered_addresses
                ):
                    self._discovered_addresses.append(address)

        addresses = {
            address
            for address in self._discovered_addresses
            if address not in current_addresses
        }

        # Check if there is at least one device
        if not addresses:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(addresses)}),
        )