async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # When coming back from the progress steps, the user_input is stored in the
        # instance variable instead of being passed in
        if user_input is None and self._user_input:
            user_input = self._user_input

        if user_input is None:
            data = self.discovery_schema or _schema_with_defaults()
            return self.async_show_form(step_id="user", data_schema=data)

        if CONF_API_KEY in user_input:
            errors = {}
            try:
                return await self._finish_config(user_input)
            except AbortFlow as err:
                raise err from None
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if errors:
                return self.async_show_form(
                    step_id="user",
                    errors=errors,
                    data_schema=_schema_with_defaults(
                        user_input.get(CONF_USERNAME),
                        user_input[CONF_HOST],
                        user_input[CONF_PORT],
                        user_input[CONF_PATH],
                        user_input[CONF_SSL],
                        user_input[CONF_VERIFY_SSL],
                    ),
                )

        self._user_input = user_input
        return await self.async_step_get_api_key()