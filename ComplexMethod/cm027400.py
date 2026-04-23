async def async_step_2fa(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle 2fa step."""
        errors = {}

        if user_input and user_input["2fa"] == "0000":
            self.tokens = await self.hive_auth.login()
        elif user_input:
            try:
                self.tokens = await self.hive_auth.sms_2fa(
                    user_input["2fa"], self.tokens
                )
            except HiveInvalid2FACode:
                errors["base"] = "invalid_code"
            except HiveApiError:
                errors["base"] = "no_internet_available"

            if not errors:
                _LOGGER.debug("2FA successful")
                if self.source == SOURCE_REAUTH:
                    return await self.async_setup_hive_entry()
                self.device_registration = True
                return await self.async_step_configuration()

        schema = vol.Schema({vol.Required(CONF_CODE): str})
        return self.async_show_form(step_id="2fa", data_schema=schema, errors=errors)