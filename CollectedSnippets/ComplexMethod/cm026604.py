async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reauth step."""
        errors: dict[str, str] = {}

        # Each model variant requires a different authentication flow
        if "Solution" in self._data[CONF_MODEL]:
            schema = STEP_AUTH_DATA_SCHEMA_SOLUTION
        elif "AMAX" in self._data[CONF_MODEL]:
            schema = STEP_AUTH_DATA_SCHEMA_AMAX
        else:
            schema = STEP_AUTH_DATA_SCHEMA_BG

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            self._data.update(user_input)
            try:
                (_, _) = await try_connect(self._data, Panel.LOAD_EXTENDED_INFO)
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
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )