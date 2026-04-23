async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm (re)authentication dialog."""
        errors: dict[str, str] = {}

        # we use this step both for initial auth and for re-auth
        reauth_entry: ConfigEntry | None = None
        if self.source == SOURCE_REAUTH:
            reauth_entry = self._get_reauth_entry()

        if user_input:
            data = {
                CONF_HOST: reauth_entry.data[CONF_HOST] if reauth_entry else self._host,
                CONF_PORT: reauth_entry.data[CONF_PORT] if reauth_entry else self._port,
                **user_input,
            }
            try:
                computer_name = await _validate_connection(data)
            except LibreHardwareMonitorConnectionError as exception:
                _LOGGER.error(exception)
                errors["base"] = "cannot_connect"
            except LibreHardwareMonitorUnauthorizedError:
                errors["base"] = "invalid_auth"
            except LibreHardwareMonitorNoDevicesError:
                errors["base"] = "no_devices"
            else:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        entry=reauth_entry,  # type: ignore[arg-type]
                        data_updates=user_input,
                    )
                # the initial connection was unauthorized, now we can create the config entry
                return self.async_create_entry(
                    title=f"{computer_name} ({self._host}:{self._port})",
                    data=data,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                REAUTH_SCHEMA,
                {
                    CONF_USERNAME: user_input[CONF_USERNAME]
                    if user_input is not None
                    else reauth_entry.data.get(CONF_USERNAME)
                    if reauth_entry is not None
                    else None
                },
            ),
            errors=errors,
        )