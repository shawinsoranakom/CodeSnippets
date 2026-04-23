async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_TOKEN) and not user_input.get(CONF_NEW_TOKEN):
                user_input[CONF_TOKEN] = sub(r"\s+", "", user_input[CONF_TOKEN])
                try:
                    await self.hass.async_add_executor_job(
                        pyotp.TOTP(user_input[CONF_TOKEN]).now
                    )
                except binascii.Error:
                    errors["base"] = "invalid_token"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(user_input[CONF_TOKEN])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=user_input,
                    )
            elif user_input.get(CONF_NEW_TOKEN):
                user_input[CONF_TOKEN] = await self.hass.async_add_executor_job(
                    pyotp.random_base32
                )
                self.user_input = user_input
                return await self.async_step_confirm()
            else:
                errors["base"] = "invalid_token"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_USER_DATA_SCHEMA, suggested_values=user_input
            ),
            errors=errors,
        )