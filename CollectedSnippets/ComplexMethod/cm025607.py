async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                (host, port, ssl) = _parse_url(user_input[CONF_URL])
            except InvalidUrl:
                errors[CONF_URL] = "invalid_url"
            else:
                try:
                    my_user_info = await check_user_info(
                        self.hass,
                        host,
                        port,
                        ssl,
                        user_input[CONF_VERIFY_SSL],
                        user_input[CONF_API_KEY],
                    )
                except ImmichUnauthorizedError:
                    errors["base"] = "invalid_auth"
                except CONNECT_ERRORS:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(my_user_info.user_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=my_user_info.name,
                        data={
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_SSL: ssl,
                            CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                            CONF_API_KEY: user_input[CONF_API_KEY],
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )