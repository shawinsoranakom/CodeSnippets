async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        data_schema = CONFIG_SCHEMA
        errors = {}

        if user_input is not None:
            if CONF_ID not in user_input:
                user_input[CONF_ID] = DEFAULT_SYSTEM_ID

            self._async_abort_entries_match(user_input)

            airzone = AirzoneLocalApi(
                aiohttp_client.async_get_clientsession(self.hass),
                ConnectionOptions(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_ID],
                ),
            )

            try:
                mac = await airzone.validate()
            except InvalidSystem:
                data_schema = SYSTEM_ID_SCHEMA
                errors[CONF_ID] = "invalid_system_id"
            except AirzoneError:
                errors["base"] = "cannot_connect"
            else:
                if mac:
                    await self.async_set_unique_id(
                        format_mac(mac), raise_on_progress=False
                    )
                    self._abort_if_unique_id_configured(
                        updates={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_PORT: user_input[CONF_PORT],
                        }
                    )

                title = f"Airzone {user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                if user_input[CONF_ID] != DEFAULT_SYSTEM_ID:
                    title += f" #{user_input[CONF_ID]}"

                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )