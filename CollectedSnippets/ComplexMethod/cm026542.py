async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconf_entry = self._get_reconfigure_entry()

        if user_input:
            try:
                await _validate_input(
                    self.hass,
                    data={
                        **reconf_entry.data,
                        **user_input,
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except FireflyClientTimeout:
                errors["base"] = "timeout_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})
                return self.async_update_reload_and_abort(
                    reconf_entry,
                    data_updates={
                        CONF_URL: user_input[CONF_URL],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_USER_DATA_SCHEMA,
                suggested_values=user_input or reconf_entry.data.copy(),
            ),
            errors=errors,
        )