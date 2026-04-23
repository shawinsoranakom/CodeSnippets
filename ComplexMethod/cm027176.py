async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        LOGGER.debug("Config entry")
        errors: dict[str, str] = {}
        if user_input:
            try:
                await validate_input(self.hass, user_input)
            except ValueError:
                # Thrown when the account id is malformed
                errors["base"] = "invalid_account"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
            else:
                await self.async_set_unique_id(user_input[CONF_ID])
                if self.source == SOURCE_USER:
                    self._abort_if_unique_id_configured()
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()

                if self.source == SOURCE_USER:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=user_input,
                    )
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ID): (
                            str
                            if self.source == SOURCE_USER
                            else self._get_reconfigure_entry().data[CONF_ID]
                        ),
                        vol.Required(
                            CONF_NAME, default=self.hass.config.location_name
                        ): str,
                        vol.Required(CONF_USERNAME): str,
                        vol.Required(CONF_PASSWORD): str,
                        vol.Optional(CONF_IS_TOU, default=False): bool,
                    }
                ),
                suggested_values=(
                    user_input or self._get_reconfigure_entry().data
                    if self.source == SOURCE_RECONFIGURE
                    else None
                ),
            ),
            errors=errors,
        )