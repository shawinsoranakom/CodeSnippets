async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        unique_id = f"{user_input[CONF_CLIENT_ID]}{user_input[CONF_ZIP_CODE]}"
        await self.async_set_unique_id(unique_id=unique_id)
        if self.source != SOURCE_REAUTH:
            self._abort_if_unique_id_configured()

        client = justnimbus.JustNimbusClient(
            client_id=user_input[CONF_CLIENT_ID], zip_code=user_input[CONF_ZIP_CODE]
        )
        try:
            await self.hass.async_add_executor_job(client.get_data)
        except justnimbus.InvalidClientID:
            errors["base"] = "invalid_auth"
        except justnimbus.JustNimbusError:
            errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if self.source != SOURCE_REAUTH:
                return self.async_create_entry(title="JustNimbus", data=user_input)
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data=user_input, unique_id=unique_id
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )