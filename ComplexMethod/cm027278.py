async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        host = user_input[CONF_HOST].rstrip("/")
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"

        data = {
            CONF_HOST: host,
            CONF_USERNAME: user_input[CONF_USERNAME],
            CONF_PASSWORD: user_input[CONF_PASSWORD],
        }
        errors = {}

        try:
            info = await validate_input(self.hass, data)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except NotSupported:
            errors["base"] = "not_supported"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )