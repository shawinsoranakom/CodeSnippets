async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the device."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            updated_host = user_input[CONF_HOST]

            self._async_abort_entries_match({CONF_HOST: updated_host})

            try:
                data_to_validate = {
                    CONF_HOST: updated_host,
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_PIN: user_input[CONF_PIN],
                    CONF_TYPE: reconfigure_entry.data.get(CONF_TYPE, BRIDGE),
                }
                if CONF_VEDO_PIN in user_input:
                    data_to_validate[CONF_VEDO_PIN] = user_input[CONF_VEDO_PIN]
                await validate_input(self.hass, data_to_validate)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidPin:
                errors["base"] = "invalid_pin"
            except InvalidVedoPin:
                errors["base"] = "invalid_vedo_pin"
            except InvalidVedoAuth:
                errors["base"] = "invalid_vedo_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                data_updates = {
                    CONF_HOST: updated_host,
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_PIN: user_input[CONF_PIN],
                }
                if CONF_VEDO_PIN in user_input:
                    data_updates[CONF_VEDO_PIN] = user_input[CONF_VEDO_PIN]
                return self.async_update_reload_and_abort(
                    reconfigure_entry, data_updates=data_updates
                )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_HOST, default=reconfigure_entry.data[CONF_HOST]
                ): cv.string,
                vol.Required(
                    CONF_PORT, default=reconfigure_entry.data[CONF_PORT]
                ): cv.port,
                vol.Optional(CONF_PIN): cv.string,
                vol.Optional(CONF_VEDO_PIN): cv.string,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )