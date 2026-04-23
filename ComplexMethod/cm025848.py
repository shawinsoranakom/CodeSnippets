async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            adv = self._discovered_devices[address][1]
            self._raise_for_advertisement_errors(adv)

            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address][0], data={}
            )

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery_info in async_discovered_service_info(self.hass, False):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            adv = Aranet4Advertisement(
                discovery_info.device, discovery_info.advertisement
            )
            if adv.manufacturer_data:
                self._discovered_devices[address] = (_title(discovery_info), adv)

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: dev[0]
                            for (addr, dev) in self._discovered_devices.items()
                        }
                    )
                }
            ),
        )