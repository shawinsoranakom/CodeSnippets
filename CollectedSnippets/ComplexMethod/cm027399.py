async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prompt user input. Create or edit entry."""
        errors: dict[str, str] = {}
        # Login to Hive with user data.
        if user_input is not None:
            self.data.update(user_input)
            self.hive_auth = Auth(
                username=self.data[CONF_USERNAME], password=self.data[CONF_PASSWORD]
            )

            # Get user from existing entry and abort if already setup
            await self.async_set_unique_id(self.data[CONF_USERNAME])
            if self.context["source"] != SOURCE_REAUTH:
                self._abort_if_unique_id_configured()

            # Login to the Hive.
            try:
                self.tokens = await self.hive_auth.login()
            except HiveInvalidUsername:
                errors["base"] = "invalid_username"
            except HiveInvalidPassword:
                errors["base"] = "invalid_password"
            except HiveApiError:
                errors["base"] = "no_internet_available"

            if (
                auth_result := self.tokens.get("AuthenticationResult", {})
            ) and auth_result.get("NewDeviceMetadata"):
                _LOGGER.debug("Login successful, New device detected")
                self.device_registration = True
                return await self.async_step_configuration()

            if self.tokens.get("ChallengeName") == "SMS_MFA":
                _LOGGER.debug("Login successful, SMS 2FA required")
                # Complete SMS 2FA.
                return await self.async_step_2fa()

            if not errors:
                _LOGGER.debug(
                    "Login successful, no new device detected, no 2FA required"
                )
                # Complete the entry.
                try:
                    return await self.async_setup_hive_entry()
                except UnknownHiveError:
                    errors["base"] = "unknown"

        # Show User Input form.
        schema = vol.Schema(
            {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)