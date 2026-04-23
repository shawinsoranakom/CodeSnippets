async def async_step_reconfigure(
        self,
        user_input: Mapping[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle reconfiguration of immich."""
        entry = self._get_reconfigure_entry()
        current_data = entry.data

        url = f"{'https' if current_data[CONF_SSL] else 'http'}://{current_data[CONF_HOST]}:{current_data[CONF_PORT]}"
        verify_ssl = current_data[CONF_VERIFY_SSL]

        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL]
            verify_ssl = user_input[CONF_VERIFY_SSL]
            try:
                (host, port, ssl) = _parse_url(user_input[CONF_URL])
            except InvalidUrl:
                errors[CONF_URL] = "invalid_url"
            else:
                try:
                    await check_user_info(
                        self.hass,
                        host,
                        port,
                        ssl,
                        user_input[CONF_VERIFY_SSL],
                        current_data[CONF_API_KEY],
                    )
                except ImmichUnauthorizedError:
                    errors["base"] = "invalid_auth"
                except CONNECT_ERRORS:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            **current_data,
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_SSL: ssl,
                            CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                        },
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=url): TextSelector(
                        config=TextSelectorConfig(type=TextSelectorType.URL)
                    ),
                    vol.Required(CONF_VERIFY_SSL, default=verify_ssl): bool,
                }
            ),
            errors=errors,
        )