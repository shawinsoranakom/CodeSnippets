async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the device."""
        reconfigure_entry = self._get_reconfigure_entry()
        if not user_input:
            return self.async_show_form(
                step_id="reconfigure", data_schema=user_form_schema(user_input)
            )

        updated_host = user_input[CONF_HOST]

        if reconfigure_entry.data[CONF_HOST] != updated_host:
            self._async_abort_entries_match({CONF_HOST: updated_host})

        errors: dict[str, str] = {}

        try:
            await validate_input(self.hass, user_input)
        except aiovodafone_exceptions.AlreadyLogged:
            errors["base"] = "already_logged"
        except aiovodafone_exceptions.CannotConnect:
            errors["base"] = "cannot_connect"
        except aiovodafone_exceptions.CannotAuthenticate:
            errors["base"] = "invalid_auth"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_update_reload_and_abort(
                reconfigure_entry, data_updates={CONF_HOST: updated_host}
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=user_form_schema(user_input),
            errors=errors,
        )