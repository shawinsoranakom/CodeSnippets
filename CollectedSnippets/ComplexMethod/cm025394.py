async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the configuration flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email: str = user_input[CONF_EMAIL]
            password: str = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            api = PyAxencoAPI(session)

            try:
                await api.login(email, password)
            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    errors["base"] = "invalid_auth"
                elif e.status >= 500:
                    errors["base"] = "cannot_connect"
                else:
                    errors["base"] = "unknown"
            except aiohttp.ClientConnectionError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"

            if not errors:
                # Prevent duplicate configuration with the same user ID
                await self.async_set_unique_id(api.user_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"MyNeomitis ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_USER_ID: api.user_id,
                    },
                )

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