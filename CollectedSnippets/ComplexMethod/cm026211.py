async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            host = self._host or user_input[CONF_HOST]
            if self.source != SOURCE_RECONFIGURE:
                self._async_abort_entries_match({CONF_HOST: host})

            _client = Client(
                TelnetConnection(
                    host,
                    user_input[CONF_PORT],
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                    timeout=10,
                )
            )

            try:
                router_info = await self.hass.async_add_executor_job(
                    _client.get_router_info
                )
            except ConnectionException:
                errors["base"] = "cannot_connect"
            else:
                if self.source == SOURCE_RECONFIGURE:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data={CONF_HOST: host, **user_input},
                    )
                return self.async_create_entry(
                    title=router_info.name, data={CONF_HOST: host, **user_input}
                )

        host_schema: VolDictType = (
            {vol.Required(CONF_HOST): str} if not self._host else {}
        )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    **host_schema,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_TELNET_PORT): int,
                }
            ),
            errors=errors,
        )