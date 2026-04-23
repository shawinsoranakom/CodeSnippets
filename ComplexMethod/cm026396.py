async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            ssl = user_input[CONF_SSL]

            protocol = "https" if ssl else "http"
            url = f"{protocol}://{host}"

            try:
                camera = await self.hass.async_add_executor_job(
                    HikCamera, url, port, username, password, ssl
                )
            except requests.exceptions.RequestException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                device_id = camera.get_id
                device_name = camera.get_name
                if device_id is None:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=device_name or host,
                        data={
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_SSL: ssl,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_SSL, default=False): bool,
                }
            ),
            errors=errors,
        )