async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}

        reauth_entry = self._get_reauth_entry()
        if user_input:
            user_input[CONF_USERNAME] = reauth_entry.data[CONF_USERNAME]
            # Reauth will use the same hardware id and re-authorise an existing
            # authorised device.
            if not self.hardware_id:
                self.hardware_id = reauth_entry.data[CONF_DEVICE_ID]
                assert self.hardware_id
            try:
                token = await validate_input(self.hass, self.hardware_id, user_input)
            except Require2FA:
                self.user_pass = user_input
                return await self.async_step_2fa()
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                data = {
                    CONF_USERNAME: user_input[CONF_USERNAME],
                    CONF_TOKEN: token,
                    CONF_DEVICE_ID: self.hardware_id,
                }
                return self.async_update_reload_and_abort(reauth_entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_USERNAME: reauth_entry.data[CONF_USERNAME],
                CONF_NAME: reauth_entry.data[CONF_USERNAME],
            },
        )