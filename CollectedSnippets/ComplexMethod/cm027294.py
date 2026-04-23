async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a Axis config flow start.

        Manage device specific parameters.
        """
        errors = {}

        if user_input is not None:
            try:
                api = await get_axis_api(self.hass, user_input)

            except AuthenticationRequired:
                errors["base"] = "invalid_auth"

            except CannotConnect:
                errors["base"] = "cannot_connect"

            else:
                serial = api.vapix.serial_number
                config = {
                    CONF_PROTOCOL: user_input[CONF_PROTOCOL],
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }

                await self.async_set_unique_id(format_mac(serial))

                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_and_abort(
                        self._get_reauth_entry(), data_updates=config
                    )
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_and_abort(
                        self._get_reconfigure_entry(), data_updates=config
                    )
                self._abort_if_unique_id_configured()

                self.config = config | {CONF_MODEL: api.vapix.product_number}

                return await self._create_entry(serial)

        data = self.discovery_schema or {
            vol.Required(CONF_PROTOCOL): vol.In(PROTOCOL_CHOICES),
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        }

        return self.async_show_form(
            step_id="user",
            description_placeholders=self.config,
            data_schema=vol.Schema(data),
            errors=errors,
        )