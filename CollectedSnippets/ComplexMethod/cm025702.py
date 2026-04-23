async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Trigger a reconfiguration flow."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()
        username = reconfigure_entry.data[CONF_USERNAME]
        await self.async_set_unique_id(username)
        if user_input:
            user_input[CONF_USERNAME] = username
            # Reconfigure will generate a new hardware id and create a new
            # authorised device at ring.com.
            if not self.hardware_id:
                self.hardware_id = str(uuid.uuid4())
            try:
                assert self.hardware_id
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
                    CONF_USERNAME: username,
                    CONF_TOKEN: token,
                    CONF_DEVICE_ID: self.hardware_id,
                }
                return self.async_update_reload_and_abort(reconfigure_entry, data=data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=STEP_RECONFIGURE_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_USERNAME: username,
            },
        )