async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            name = user_input[CONF_NAME]

            discovered = self._discovered_devices[name]

            assert discovered is not None

            self._discovery = discovered

            if not discovered.device.is_pairing:
                return await self.async_step_wait_for_pairing_mode()

            address = discovered.info.address
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self._create_snooz_entry(discovered)

        configured_addresses = self._async_current_ids(include_ignore=False)

        for info in async_discovered_service_info(self.hass):
            address = info.address
            if address in configured_addresses:
                continue
            device = SnoozAdvertisementData()
            if device.supported(info):
                assert device.display_name
                self._discovered_devices[device.display_name] = DiscoveredSnooz(
                    info, device
                )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): vol.In(
                        [
                            d.device.display_name
                            for d in self._discovered_devices.values()
                        ]
                    )
                }
            ),
        )