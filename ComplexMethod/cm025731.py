async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initialize form."""
        errors: dict[str, str] = {}
        if user_input is not None:
            authentication = CONF_USERNAME in user_input or CONF_PASSWORD in user_input
            if authentication and CONF_USERNAME not in user_input:
                errors["base"] = "username_missing"
            if authentication and CONF_PASSWORD not in user_input:
                errors["base"] = "password_missing"
            if user_input[CONF_CONTRIBUTING_USER] and not authentication:
                errors["base"] = "no_authentication"
            if authentication and not errors:
                opensky = OpenSky(session=async_get_clientsession(self.hass))
                try:
                    await opensky.authenticate(
                        BasicAuth(
                            login=user_input[CONF_USERNAME],
                            password=user_input[CONF_PASSWORD],
                        ),
                        contributing_user=user_input[CONF_CONTRIBUTING_USER],
                    )
                except OpenSkyUnauthenticatedError:
                    errors["base"] = "invalid_auth"
            if not errors:
                return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_RADIUS): vol.Coerce(float),
                        vol.Optional(CONF_ALTITUDE): vol.Coerce(float),
                        vol.Optional(CONF_USERNAME): str,
                        vol.Optional(CONF_PASSWORD): str,
                        vol.Optional(CONF_CONTRIBUTING_USER, default=False): bool,
                    }
                ),
                user_input or self.config_entry.options,
            ),
        )