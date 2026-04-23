async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=user_form_schema(user_input)
            )

        # Use host because no serial number or mac is available to use for a unique id
        self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except aiovodafone_exceptions.AlreadyLogged:
            errors["base"] = "already_logged"
        except aiovodafone_exceptions.CannotConnect:
            errors["base"] = "cannot_connect"
        except aiovodafone_exceptions.CannotAuthenticate:
            errors["base"] = "invalid_auth"
        except aiovodafone_exceptions.ModelNotSupported:
            errors["base"] = "model_not_supported"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=info["title"],
                data=user_input | {CONF_DEVICE_DETAILS: info[CONF_DEVICE_DETAILS]},
            )

        return self.async_show_form(
            step_id="user", data_schema=user_form_schema(user_input), errors=errors
        )