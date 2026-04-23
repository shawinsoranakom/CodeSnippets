async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Check if paired."""
        errors: dict[str, str] = {}

        if discovery := self._discovered_adv:
            self._discovered_advs[discovery.address] = discovery
        else:
            current_addresses = self._async_current_ids(include_ignore=False)
            for discovery_info in async_discovered_service_info(self.hass):
                self._ble_device = discovery_info.device
                address = discovery_info.address
                if address in current_addresses or address in self._discovered_advs:
                    continue
                parsed = parse_advertisement_data(
                    discovery_info.device, discovery_info.advertisement
                )
                if parsed:
                    self._discovered_adv = parsed
                    self._discovered_advs[address] = parsed

        if not self._discovered_advs:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            self._name = name_from_discovery(self._discovered_adv)
            self._bdaddr = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(self._bdaddr, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self.async_step_link()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{parsed.data['local_name']} ({address})"
                            for address, parsed in self._discovered_advs.items()
                        }
                    )
                }
            ),
            errors=errors,
        )