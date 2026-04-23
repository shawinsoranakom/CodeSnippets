async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        self._async_abort_entries_match({CONF_API_KEY: user_input[CONF_API_KEY]})

        try:
            info = await validate_api(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidKey:
            errors["base"] = "invalid_auth_key"
        except InvalidSecret:
            errors["base"] = "invalid_auth_secret"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )