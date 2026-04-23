async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.email = user_input[CONF_EMAIL]
            self.password = user_input[CONF_PASSWORD]
            self.verisure = Verisure(
                username=self.email,
                password=self.password,
                cookie_file_name=self.hass.config.path(
                    STORAGE_DIR, f"verisure_{user_input[CONF_EMAIL]}"
                ),
            )

            try:
                await self.hass.async_add_executor_job(self.verisure.login)
            except VerisureLoginError as ex:
                if "Multifactor authentication enabled" in str(ex):
                    try:
                        await self.hass.async_add_executor_job(
                            self.verisure.request_mfa
                        )
                    except (
                        VerisureLoginError,
                        VerisureError,
                        VerisureResponseError,
                    ) as mfa_ex:
                        LOGGER.debug(
                            "Unexpected response from Verisure during MFA set up, %s",
                            mfa_ex,
                        )
                        errors["base"] = "unknown_mfa"
                    else:
                        return await self.async_step_mfa()
                else:
                    LOGGER.debug("Could not log in to Verisure, %s", ex)
                    errors["base"] = "invalid_auth"
            except (VerisureError, VerisureResponseError) as ex:
                LOGGER.debug("Unexpected response from Verisure, %s", ex)
                errors["base"] = "unknown"
            else:
                return await self.async_step_installation()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )