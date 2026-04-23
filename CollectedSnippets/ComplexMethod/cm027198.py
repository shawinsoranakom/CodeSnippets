async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            if CONF_VERIFY_SSL not in user_input:
                user_input[CONF_VERIFY_SSL] = DEFAULT_VERIFY_SSL

            try:
                await self.hass.async_add_executor_job(_validate_input, user_input)
            except NZBGetAPIException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        data_schema = {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Optional(CONF_USERNAME): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
        }

        if self.show_advanced_options:
            data_schema[vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL)] = (
                bool
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors or {},
        )