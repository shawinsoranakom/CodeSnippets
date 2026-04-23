async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)

            if api_key and not (username or password):
                # Use the user-supplied API key to attempt to obtain a PIN from ecobee.
                self._ecobee = Ecobee(config={ECOBEE_API_KEY: api_key})
                if await self.hass.async_add_executor_job(self._ecobee.request_pin):
                    # We have a PIN; move to the next step of the flow.
                    return await self.async_step_authorize()
                errors["base"] = "pin_request_failed"
            elif username and password and not api_key:
                self._ecobee = Ecobee(
                    config={
                        ECOBEE_USERNAME: username,
                        ECOBEE_PASSWORD: password,
                    }
                )
                if await self.hass.async_add_executor_job(self._ecobee.refresh_tokens):
                    config = {
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                        CONF_REFRESH_TOKEN: self._ecobee.refresh_token,
                    }
                    return self.async_create_entry(title=DOMAIN, data=config)
                errors["base"] = "login_failed"
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=_USER_SCHEMA,
            errors=errors,
        )