async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info[KEY_SYS_SERIAL])
                if self.source != SOURCE_REAUTH:
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=info[KEY_SYS_TITLE], data=user_input
                    )
                self._abort_if_unique_id_mismatch(reason="invalid_host")
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data=user_input
                )

        data_schema = DATA_SCHEMA
        if self.source == SOURCE_REAUTH:
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self._get_reauth_entry().data
            )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )