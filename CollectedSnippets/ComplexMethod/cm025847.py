async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication confirmation."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            updates = {
                CONF_USERNAME: user_input.get(CONF_USERNAME) or None,
                CONF_PASSWORD: user_input.get(CONF_PASSWORD) or None,
                CONF_SSL: user_input.get(
                    CONF_SSL, reauth_entry.data.get(CONF_SSL, False)
                ),
            }
            try:
                await validate_input({**reauth_entry.data, **updates})
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauthentication")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates=updates,
                )

        suggested_values = {
            CONF_USERNAME: reauth_entry.data.get(CONF_USERNAME, None),
            CONF_SSL: reauth_entry.data.get(CONF_SSL, False),
        }
        if user_input is not None:
            suggested_values.update(user_input)
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_REAUTH_DATA_SCHEMA, suggested_values
            ),
            description_placeholders={CONF_HOST: reauth_entry.data[CONF_HOST]},
            errors=errors,
        )