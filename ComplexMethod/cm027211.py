async def async_step_machine_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let user select machine to connect to."""
        errors: dict[str, str] = {}
        if user_input:
            if not self._discovered:
                serial_number = user_input[CONF_MACHINE]
                if self.source != SOURCE_RECONFIGURE:
                    await self.async_set_unique_id(serial_number)
                    self._abort_if_unique_id_configured()
            else:
                serial_number = self._discovered[CONF_MACHINE]

            selected_device = self._things[serial_number]

            if not errors:
                if self.source == SOURCE_RECONFIGURE:
                    for service_info in async_discovered_service_info(self.hass):
                        if service_info.name.startswith(BT_MODEL_PREFIXES):
                            self._discovered[service_info.name] = service_info.address

                    if self._discovered:
                        return await self.async_step_bluetooth_selection()
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=self._config,
                    )

                return self.async_create_entry(
                    title=selected_device.name,
                    data={
                        **self._config,
                        CONF_INSTALLATION_KEY: self._installation_key.to_json(),
                        CONF_TOKEN: self._things[serial_number].ble_auth_token,
                    },
                )

        machine_options = [
            SelectOptionDict(
                value=thing.serial_number,
                label=f"{thing.name} ({thing.serial_number})",
            )
            for thing in self._things.values()
        ]

        machine_selection_schema = vol.Schema(
            {
                vol.Required(
                    CONF_MACHINE, default=machine_options[0]["value"]
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=machine_options,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="machine_selection",
            data_schema=machine_selection_schema,
            errors=errors,
        )