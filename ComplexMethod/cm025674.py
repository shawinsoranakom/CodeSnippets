async def async_step_network(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle network step."""
        step_errors: dict[str, str] = {}
        if user_input is not None:
            self._title = "Velbus Network"
            if user_input[CONF_TLS]:
                self._device = "tls://"
            else:
                self._device = ""
            if CONF_PASSWORD in user_input and user_input[CONF_PASSWORD] != "":
                self._device += f"{user_input[CONF_PASSWORD]}@"
            self._device += f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            if self.source != SOURCE_RECONFIGURE:
                self._async_abort_entries_match({CONF_PORT: self._device})
            if await self._test_connection():
                return await self.async_step_vlp()
            step_errors[CONF_HOST] = "cannot_connect"
        elif self.source == SOURCE_RECONFIGURE:
            current = self._get_reconfigure_entry().data.get(CONF_PORT, "")
            tls = current.startswith("tls://")
            current = current.removeprefix("tls://")
            if "@" in current:
                password, host_port = current.split("@", 1)
            else:
                password = ""
                host_port = current
            host, _, port = host_port.rpartition(":")
            user_input = {
                CONF_TLS: tls,
                CONF_HOST: host,
                CONF_PORT: int(port) if port.isdigit() else 27015,
            }
            if password:
                user_input[CONF_PASSWORD] = password
        else:
            user_input = {
                CONF_TLS: True,
                CONF_PORT: 27015,
            }

        return self.async_show_form(
            step_id="network",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_TLS): bool,
                        vol.Required(CONF_HOST): str,
                        vol.Required(CONF_PORT): int,
                        vol.Optional(CONF_PASSWORD): str,
                    }
                ),
                suggested_values=user_input,
            ),
            errors=step_errors,
        )