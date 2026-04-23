async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the auth step."""
        errors: dict[str, str] = {}

        # Each model variant requires a different authentication flow
        if "Solution" in self._data[CONF_MODEL]:
            schema = STEP_AUTH_DATA_SCHEMA_SOLUTION
        elif "AMAX" in self._data[CONF_MODEL]:
            schema = STEP_AUTH_DATA_SCHEMA_AMAX
        else:
            schema = STEP_AUTH_DATA_SCHEMA_BG

        if user_input is not None:
            self._data.update(user_input)
            try:
                (model, serial_number) = await try_connect(
                    self._data, Panel.LOAD_EXTENDED_INFO
                )
            except (PermissionError, ValueError) as e:
                errors["base"] = "invalid_auth"
                _LOGGER.error("Authentication Error: %s", e)
            except (
                OSError,
                ConnectionRefusedError,
                ssl.SSLError,
                TimeoutError,
            ) as e:
                _LOGGER.error("Connection Error: %s", e)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if serial_number:
                    await self.async_set_unique_id(str(serial_number))
                if self.source in (SOURCE_USER, SOURCE_DHCP):
                    if serial_number:
                        self._abort_if_unique_id_configured()
                    else:
                        self._async_abort_entries_match(
                            {CONF_HOST: self._data[CONF_HOST]}
                        )
                    return self.async_create_entry(
                        title=f"Bosch {model}", data=self._data
                    )
                if serial_number:
                    self._abort_if_unique_id_mismatch(reason="device_mismatch")

                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data=self._data,
                )

        return self.async_show_form(
            step_id="auth",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )