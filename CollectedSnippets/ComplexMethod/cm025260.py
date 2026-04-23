async def async_step_discovered_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self._discovered_ip is not None
        assert self._discovered_mac is not None

        errors = {}
        base_schema = {vol.Required(CONF_PORT, default=DEFAULT_PORT): int}

        if user_input is not None:
            airzone = AirzoneLocalApi(
                aiohttp_client.async_get_clientsession(self.hass),
                ConnectionOptions(
                    self._discovered_ip,
                    user_input[CONF_PORT],
                    user_input.get(CONF_ID, DEFAULT_SYSTEM_ID),
                ),
            )

            try:
                mac = await airzone.validate()
            except InvalidSystem:
                base_schema[vol.Required(CONF_ID, default=1)] = int
                errors[CONF_ID] = "invalid_system_id"
            except AirzoneError:
                errors["base"] = "cannot_connect"
            else:
                user_input[CONF_HOST] = self._discovered_ip

                if mac is None:
                    mac = self._discovered_mac

                await self.async_set_unique_id(format_mac(mac))
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    }
                )

                title = f"Airzone {short_mac(mac)}"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="discovered_connection",
            data_schema=vol.Schema(base_schema),
            errors=errors,
        )